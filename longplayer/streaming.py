import time
import shout
import queue
import lameenc
import logging
import threading
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger("longplayer")


@dataclass
class IcecastConfig:
    host: str
    mount: str
    port: int
    user: str
    password: str


class LongplayerIcecastStreamer:
    def __init__(self, icecast_config: IcecastConfig = None):
        self.config = icecast_config
        self.is_running = False
        self.thread = None

        # --------------------------------------------------------------------------------
        # Create Icecast client
        # --------------------------------------------------------------------------------
        self.client = shout.Shout()
        self.client.host = icecast_config.host
        self.client.mount = icecast_config.mount
        self.client.port = icecast_config.port
        self.client.user = icecast_config.user
        self.client.password = icecast_config.password
        self.client.format = "mp3"

        # --------------------------------------------------------------------------------
        # Create mp3 encoder
        # --------------------------------------------------------------------------------
        self.encoder = lameenc.Encoder()
        self.encoder.set_bit_rate(256)
        self.encoder.set_channels(2)
        self.encoder.set_in_sample_rate(44100)
        self.encoder.set_quality(2)  # 2 = highest, 7 = fastest
        self.queue = queue.Queue()

        logger.debug("Streamer: Initialized Icecast streamer and mp3 encoder")

    def step(self):
        try:
            block = self.queue.get(block=False)
        except queue.Empty:
            return

        # --------------------------------------------------------------------------------
        # Take first two channels of output, convert to int16, flatten and interleave.
        # TODO: This assumes stereo output; modify as needed for different channel counts.
        # --------------------------------------------------------------------------------
        samples = (block * 32768).astype(np.int16)
        samples = samples.flatten()

        # --------------------------------------------------------------------------------
        # Encode as mp3
        # --------------------------------------------------------------------------------
        encoded = self.encoder.encode(samples)
        encoded = bytes(encoded)

        # --------------------------------------------------------------------------------
        # Send to Icecast server and wait until next block required
        # --------------------------------------------------------------------------------
        logger.debug("Streamer: Sending block (%d bytes)" % len(encoded))
        self.client.send(encoded)
        self.client.sync()

    def runloop(self):
        while self.is_running:
            self.step()
            time.sleep(0.005)

    def start(self):
        self.is_running = True

        try:
            self.client.open()
        except shout.ShoutException as e:
            raise e
        
        logger.info("Streamer: Connected to Icecast server at %s:%d%s" % (self.config.host,
                                                                          self.config.port,
                                                                          self.config.mount))

        self.client.set_metadata({
            "song": "Longplayer"
        })
        self.thread = threading.Thread(target=self.runloop,
                                       daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
        self.thread.join()
        logger.info("Streamer: Disconnected from Icecast server")

    def push_block(self, block: np.ndarray):
        self.queue.put(block)
