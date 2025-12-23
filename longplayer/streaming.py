import os
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
        self.is_connected = False
        self.thread = None

        # --------------------------------------------------------------------------------
        # Create mp3 encoder
        # --------------------------------------------------------------------------------
        self.encoder = lameenc.Encoder()
        self.encoder.set_bit_rate(256)
        self.encoder.set_channels(2)
        self.encoder.set_in_sample_rate(44100)
        self.encoder.set_quality(2)  # 2 = highest, 7 = fastest
        self.queue = queue.Queue()

        logger.debug("Streamer: Initialized mp3 encoder")

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
        self.is_running = True
        try:
            self.connect()
            self.is_connected = True
        except shout.ShoutException as e:
            logger.error("Streamer: Failed to connect to Icecast server: %s" % str(e))
            os._exit(1)

        while self.is_running:
            try:
                self.step()
            except shout.ShoutException as e:
                logger.error("Streamer: Connection lost: %s" % str(e))
                self.client.close()
                self.is_connected = False

                #--------------------------------------------------------------------------------
                # Attempt reconnection with 5-second delay between attempts
                #--------------------------------------------------------------------------------
                while not self.is_connected and self.is_running:
                    try:
                        time.sleep(5)
                        logger.info("Streamer: Attempting reconnection to Icecast server...")
                        self.connect()
                        self.is_connected = True
                    except shout.ShoutException as e:
                        logger.error("Streamer: Reconnection failed (%s)" % str(e))
            time.sleep(0.005)
    
    def connect(self):
        try:
            logger.debug("Streamer: Connecting to Icecast server at %s:%d%s..." % (self.config.host, 
                                                                                  self.config.port, 
                                                                                  self.config.mount))
            
            # --------------------------------------------------------------------------------
            # Create Icecast client
            # --------------------------------------------------------------------------------
            self.client = shout.Shout()
            self.client.host = self.config.host
            self.client.mount = self.config.mount
            self.client.port = self.config.port
            self.client.user = self.config.user
            self.client.password = self.config.password
            self.client.format = "mp3"
            self.client.open()
        except shout.ShoutException as e:
            raise e
        
        logger.info("Streamer: Connected to Icecast server at %s:%d%s" % (self.config.host,
                                                                          self.config.port,
                                                                          self.config.mount))

        self.client.set_metadata({
            "song": "Longplayer"
        })        

    def start(self):
        self.thread = threading.Thread(target=self.runloop,
                                       daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
        self.thread.join()
        logger.info("Streamer: Disconnected from Icecast server")

    def push_block(self, block: np.ndarray):
        self.queue.put(block)
