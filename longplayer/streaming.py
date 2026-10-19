import math
import time
import shout
import queue
import lameenc
import logging
import threading
import numpy as np
from dataclasses import dataclass
from .constants import SAMPLE_RATE

logger = logging.getLogger("longplayer")

#--------------------------------------------------------------------------------
# mp3 bitrate, in kbps
#--------------------------------------------------------------------------------
STREAM_BITRATE = 256

#--------------------------------------------------------------------------------
# Maximum duration of audio to hold in the queue between the render thread
# and the streamer thread. If the streamer falls behind (e.g. while disconnected),
# the oldest audio is discarded so that memory usage stays bounded.
#--------------------------------------------------------------------------------
STREAM_QUEUE_DURATION = 2.0

#--------------------------------------------------------------------------------
# Time to wait for the Icecast server to accept a connection.
#--------------------------------------------------------------------------------
STREAM_CONNECT_TIMEOUT = 10.0

#--------------------------------------------------------------------------------
# Maximum duration of encoded audio that may back up in libshout's send queue
# before the connection is considered dead. This catches network failures in
# which the server silently stops accepting data without closing the socket.
#--------------------------------------------------------------------------------
STREAM_SEND_TIMEOUT = 10.0

#--------------------------------------------------------------------------------
# Delay between reconnection attempts.
#--------------------------------------------------------------------------------
STREAM_RECONNECT_INTERVAL = 5.0

#--------------------------------------------------------------------------------
# Interval between periodic status log messages.
#--------------------------------------------------------------------------------
STREAM_STATUS_INTERVAL = 60.0


@dataclass
class IcecastConfig:
    host: str
    mount: str
    port: int
    user: str
    password: str


class StreamerError(Exception):
    pass


class LongplayerIcecastStreamer:
    def __init__(self, icecast_config: IcecastConfig = None, block_size: int = 4096):
        """
        Initialize the Longplayer Icecast streamer with the specified Icecast configuration.

        Args:
            icecast_config (IcecastConfig): Configuration for connecting to the Icecast server.
            block_size (int): Number of frames in each block passed to push_block().
        """
        self.config = icecast_config
        self.client = None
        self.encoder = None
        self.thread = None
        self.stop_event = threading.Event()
        self.dropped_blocks = 0

        max_queue_blocks = max(2, math.ceil(STREAM_QUEUE_DURATION * SAMPLE_RATE / block_size))
        self.queue = queue.Queue(maxsize=max_queue_blocks)

    def create_encoder(self):
        """
        Create a new mp3 encoder. A fresh encoder is used for each connection.
        """
        encoder = lameenc.Encoder()
        encoder.set_bit_rate(STREAM_BITRATE)
        encoder.set_channels(2)
        encoder.set_in_sample_rate(SAMPLE_RATE)
        encoder.set_quality(2)  # 2 = highest, 7 = fastest
        return encoder

    def step(self):
        """
        Process the next block of audio from the queue, encode it as mp3, and send it
        to the Icecast server.

        Pacing is provided by the render thread, which produces blocks in real time
        as the audio hardware consumes them, so there is no need to call client.sync().

        Raises:
            shout.ShoutException: If there is an error sending data to the Icecast server.
            StreamerError: If the server has stopped accepting data.
        """
        try:
            block = self.queue.get(timeout=0.1)
        except queue.Empty:
            return

        # --------------------------------------------------------------------------------
        # Convert to int16, clipping to avoid wraparound, then flatten to interleave.
        # --------------------------------------------------------------------------------
        samples = (np.clip(block, -1.0, 1.0) * 32767).astype(np.int16)
        samples = samples.flatten()

        # --------------------------------------------------------------------------------
        # Encode as mp3
        # --------------------------------------------------------------------------------
        encoded = bytes(self.encoder.encode(samples))
        if not encoded:
            return

        # --------------------------------------------------------------------------------
        # Send to Icecast server. The client is non-blocking, so if the network stalls,
        # data accumulates in libshout's queue rather than blocking indefinitely.
        # --------------------------------------------------------------------------------
        self.client.send(encoded)

        backlog_bytes = self.client.queuelen()
        max_backlog_bytes = STREAM_SEND_TIMEOUT * STREAM_BITRATE * 1000 / 8
        if backlog_bytes > max_backlog_bytes:
            raise StreamerError("Server not accepting data (%d bytes queued)" % backlog_bytes)

    def runloop(self):
        """
        Main loop for the Icecast streamer. Continuously processes audio blocks and handles
        reconnections to the Icecast server if the connection fails or is lost.
        """
        while not self.stop_event.is_set():
            try:
                self.connect()
            except (shout.ShoutException, StreamerError) as e:
                self.disconnect()
                if self.stop_event.is_set():
                    break
                logger.error("Streamer: Failed to connect to Icecast server (%s), retrying in %ds" %
                             (str(e), STREAM_RECONNECT_INTERVAL))
                self.stop_event.wait(STREAM_RECONNECT_INTERVAL)
                continue

            #--------------------------------------------------------------------------------
            # Discard audio that accumulated while disconnected, so that the stream
            # resumes with live audio.
            #--------------------------------------------------------------------------------
            self.clear_queue()
            last_status_time = time.monotonic()

            try:
                while not self.stop_event.is_set():
                    self.step()
                    if time.monotonic() - last_status_time >= STREAM_STATUS_INTERVAL:
                        logger.debug("Streamer: Status: %d blocks queued, %d bytes unsent, %d blocks dropped" %
                                     (self.queue.qsize(), self.client.queuelen(), self.dropped_blocks))
                        last_status_time = time.monotonic()
            except (shout.ShoutException, StreamerError) as e:
                logger.error("Streamer: Connection lost (%s)" % str(e))
            except Exception:
                logger.exception("Streamer: Unexpected error")
            finally:
                self.disconnect()

            if not self.stop_event.is_set():
                self.stop_event.wait(STREAM_RECONNECT_INTERVAL)
                logger.info("Streamer: Attempting reconnection to Icecast server...")

    def connect(self):
        """
        Establish a connection to the Icecast server using the provided configuration.

        Raises:
            shout.ShoutException: If there is an error connecting to the Icecast server.
            StreamerError: If the connection times out or is refused by the server.
        """
        logger.debug("Streamer: Connecting to Icecast server at %s:%d%s..." % (self.config.host,
                                                                              self.config.port,
                                                                              self.config.mount))

        # --------------------------------------------------------------------------------
        # Create Icecast client.
        # Use non-blocking mode so that neither connecting nor sending can hang
        # indefinitely if the server or network becomes unresponsive.
        # --------------------------------------------------------------------------------
        self.client = self.create_client()
        self.client.nonblocking = True
        self.client.open()

        deadline = time.monotonic() + STREAM_CONNECT_TIMEOUT
        while self.client.get_connected() == shout.SHOUTERR_BUSY:
            if time.monotonic() > deadline:
                raise StreamerError("Timed out")
            if self.stop_event.wait(0.05):
                raise StreamerError("Streamer stopped")
        status = self.client.get_connected()
        if status != shout.SHOUTERR_CONNECTED:
            raise StreamerError("Connection refused by server (error %d)" % status)

        self.encoder = self.create_encoder()

        logger.info("Streamer: Connected to Icecast server at %s:%d%s" % (self.config.host,
                                                                          self.config.port,
                                                                          self.config.mount))

        # --------------------------------------------------------------------------------
        # set_metadata() makes a separate, blocking HTTP request, which can hang if the
        # server is unresponsive. Send it from a separate client on a background thread
        # so that it cannot stall the stream.
        # --------------------------------------------------------------------------------
        threading.Thread(target=self.send_metadata, daemon=True).start()

    def create_client(self) -> shout.Shout:
        client = shout.Shout()
        client.host = self.config.host
        client.mount = self.config.mount
        client.port = self.config.port
        client.user = self.config.user
        client.password = self.config.password
        client.format = "mp3"
        return client

    def send_metadata(self):
        try:
            self.create_client().set_metadata({
                "song": "Longplayer"
            })
        except shout.ShoutException as e:
            logger.warning("Streamer: Failed to set metadata (%s)" % str(e))

    def disconnect(self):
        """
        Close the connection to the Icecast server, if open.
        """
        if self.client is not None:
            try:
                self.client.close()
            except shout.ShoutException:
                pass
            self.client = None

    def clear_queue(self):
        while True:
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break

    def start(self):
        """
        Start the Icecast streamer in a separate thread.
        """
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.runloop,
                                       daemon=True)
        self.thread.start()

    def stop(self):
        """
        Stop the Icecast streamer and wait for the streaming thread to finish.
        """
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=STREAM_CONNECT_TIMEOUT)
            self.thread = None
        logger.info("Streamer: Disconnected from Icecast server")

    def push_block(self, block: np.ndarray):
        """
        Push a block of audio data into the streaming queue.
        Never blocks: if the queue is full, the oldest block is discarded.

        Args:
            block (np.ndarray): A 2-dimensional array of floating-point audio samples,
                                of shape (num_frames, 2).
        """
        while True:
            try:
                self.queue.put_nowait(block)
                return
            except queue.Full:
                try:
                    self.queue.get_nowait()
                    self.dropped_blocks += 1
                except queue.Empty:
                    pass
