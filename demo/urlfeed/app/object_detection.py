#!/usr/bin/env python
# coding: utf-8

# ##### Copyright 2018 The TensorFlow Hub Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# Copyright 2018 The TensorFlow Hub Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================


# # Object detection
#
# <table align="left"><td>
#   <a target="_blank"  href="https://colab.research.google.com/github/tensorflow/hub/blob/master/examples/colab/object_detection.ipynb">
#     <img src="https://www.tensorflow.org/images/colab_logo_32px.png" />Run in Google Colab
#   </a>
# </td><td>
#   <a target="_blank"  href="https://github.com/tensorflow/hub/blob/master/examples/colab/object_detection.ipynb">
#     <img width=32px src="https://www.tensorflow.org/images/GitHub-Mark-32px.png" />View source on GitHub</a>
# </td></table>
#


# @title Imports and function definitions

# For running inference on the TF-Hub module.
import tensorflow as tf
import tensorflow_hub as hub

import numpy as np
from queue import Queue
import threading

# For measuring the inference time.
import time
import os
import cv2

class objectDetectionModel:
    def __init__(self):
        # Pick an object detection module and set it up
        # @param ["https://tfhub.dev/google/openimages_v4/ssd/mobilenet_v2/1", "https://tfhub.dev/google/faster_rcnn/openimages_v4/inception_resnet_v2/1"]
        self.module_handle = "https://tfhub.dev/google/openimages_v4/ssd/mobilenet_v2/1"
        self.session = None
        self.result = None
        self.input_image = None
        self.stopInference = False
        self.inQ = None
        self.outQ = None
        self.input_url = None
        self.egressPipe = None
        self.inQ_max_size = 500

    def setup(self):
        with tf.Graph().as_default():
            detector = hub.Module(self.module_handle)
            self.input_image = tf.placeholder(tf.float32)
            # Module accepts as input tensors of shape [1, height, width, 3], i.e. batch
            # of size 1 and type tf.float32.
            module_input = tf.expand_dims(self.input_image, 0)
            self.result = detector(module_input, as_dict=True)
            init_ops = [tf.global_variables_initializer(),
                        tf.tables_initializer()]

            self.session = tf.Session()
            self.session.run(init_ops)

    def read_frame(self):
        cap = cv2.VideoCapture(self.input_url)
        while not self.stopInference:
            # Capture frame-by-frame
            ret, frame = cap.read()
            if not ret:
                print(ret)
                self.inQ.put(None)
                break
            # convert to low resolution to improve the inference latency - 640x360
            frame = cv2.resize(frame, (640, 360))
            # Wait till the queue has space to put new frame
            while (self.inQ.full()) and (not self.stopInference):
                time.sleep(0.1)
            if self.stopInference:
                break
            self.inQ.put(frame)
        cap.release()
        if self.stopInference:
            print("Stopped reading frames from youtube url")
        else:
            print("Done reading frames from youtube url")
        self.inQ.put(None)

    def draw_bounding_box_on_image(self, image, left, top, right, bottom, detection_class):
        cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)
        x = left
        y = top - 10
        if y < 0:
            y = 0
        x_offset = len(detection_class) * 14
        cv2.rectangle(image, (x, top-25), (x+x_offset, top),
                      (243, 109, 33), cv2.FILLED)
        cv2.putText(image, detection_class, (x, y),
                    cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)

    def write_frame(self):
        out = open(self.egressPipe, "wb")
        max_boxes = 5
        while not self.stopInference:
            output = self.outQ.get()
            if output is None:
                break
            image = output['image']
            im_height, im_width, channels = image.shape
            result_out = output['result']

            scores = result_out["detection_scores"]
            order = np.argsort(scores)[::-1]

            scores = scores[order]
            boxes = result_out["detection_boxes"][order,:]
            detection_classes = result_out["detection_class_entities"][order]

            for i in range(min(boxes.shape[0], max_boxes)):
                if scores[i] < 0.3:
                    continue
                ymin, xmin, ymax, xmax = boxes[i]
                (left, right, top, bottom) = (xmin * im_width, xmax * im_width,
                                              ymin * im_height, ymax * im_height)
                self.draw_bounding_box_on_image(image, int(left.item()), int(top.item()), int(
                    right.item()), int(bottom.item()), detection_classes[i].decode("ascii"))
            ret, image_string = cv2.imencode(".jpg", image)
            out.write(image_string.tostring())
        if self.stopInference:
            print("Stopped writing frames")
        else:
            print("Done writing frames")
        out.close()

    def infer(self, input_url, egressPipe):
        count = 0
        result_out = None
        self.egressPipe = egressPipe
        self.input_url = input_url
        self.inQ = Queue(self.inQ_max_size)
        self.outQ = Queue()
        write_thr = threading.Thread(target=self.write_frame)
        write_thr.name = "inferenceWrite"
        write_thr.daemon = True
        write_thr.start()

        read_thr = threading.Thread(target=self.read_frame)
        read_thr.name = "inferenceRead"
        read_thr.daemon = True
        read_thr.start()

        while not self.stopInference:
            frame = self.inQ.get()
            if frame is None:
                print("Frame is None ,breaking from loop")
                break
            '''
            To speed up inference, execute the inference logic on every 10th frame
            and reuse the same inference results on other frames.
            '''
            if count % 10 == 0:
                input_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) / 255.0
                result_out = self.session.run(
                    [self.result],
                    feed_dict={self.input_image: input_image})
            self.outQ.put({"image": frame, "result": result_out[0]})
            count = count + 1
        self.outQ.put(None)
        print("Waiting for read and write frame threads to finish")
        # Wait till readFrame and writeFrame threads are completed
        read_thr.join()
        write_thr.join()
        if self.stopInference:
            print("Stopped inference")
        else:
            print("Done with inference")
