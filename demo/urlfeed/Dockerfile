FROM tensorflow/tensorflow:1.12.0-py3

RUN groupadd -r dev && useradd -r -g dev dev && mkdir /url-feed && chown dev:dev /url-feed && mkdir /url-feed/uwsgi

RUN apt-get update

# Core linux dependencies.
RUN apt-get install -y \
        build-essential \
        libpcre3 \
        libpcre3-dev \
        cmake \
        git \
        wget \
        unzip \
        yasm \
        pkg-config \
        libswscale-dev \
        libtbb2 \
        libtbb-dev \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        libjasper-dev \
        libavformat-dev \
        libhdf5-dev \
        libpq-dev \
        ffmpeg

# Python dependencies
RUN pip3 --no-cache-dir install \
    numpy \
    youtube_dl \
    pafy

WORKDIR /
ENV OPENCV_VERSION="3.4.1"
RUN wget https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.zip \
&& unzip ${OPENCV_VERSION}.zip \
&& mkdir /opencv-${OPENCV_VERSION}/cmake_binary \
&& cd /opencv-${OPENCV_VERSION}/cmake_binary \
&& cmake -DBUILD_TIFF=ON \
  -DBUILD_opencv_java=OFF \
  -DWITH_CUDA=OFF \
  -DENABLE_AVX=ON \
  -DWITH_OPENGL=ON \
  -DWITH_OPENCL=ON \
  -DWITH_IPP=ON \
  -DWITH_TBB=ON \
  -DWITH_EIGEN=ON \
  -DWITH_V4L=ON \
  -DBUILD_TESTS=OFF \
  -DBUILD_PERF_TESTS=OFF \
  -DCMAKE_BUILD_TYPE=RELEASE \
  -DCMAKE_INSTALL_PREFIX=$(python3 -c "import sys; print(sys.prefix)") \
  -DPYTHON_EXECUTABLE=$(which python3) \
  -DPYTHON_INCLUDE_DIR=$(python3 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
  -DPYTHON_PACKAGES_PATH=$(python3 -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") .. \
&& make install \
&& rm /${OPENCV_VERSION}.zip \
&& rm -r /opencv-${OPENCV_VERSION}

RUN pip3 install flask uwsgi
RUN pip3 install  tensorflow_hub
RUN mkdir -p /url-feed/run && mkfifo /url-feed/run/input_video && mkfifo /url-feed/run/inference.mkv

RUN mkdir -p /usr/share/fonts/truetype/liberation
COPY third-party/LiberationSansNarrow-Regular.ttf /usr/share/fonts/truetype/liberation/LiberationSansNarrow-Regular.ttf
RUN mkdir -p /tfhub/f34b2684786cf6de38511148638abf91283beb1f
RUN wget https://storage.googleapis.com/tfhub-modules/google/openimages_v4/ssd/mobilenet_v2/1.tar.gz
RUN tar -xzvf 1.tar.gz -C /tfhub/f34b2684786cf6de38511148638abf91283beb1f
COPY --chown=dev:dev app/*.py /url-feed/
COPY uwsgi/uwsgi.ini /url-feed/uwsgi/uwsgi.ini

CMD ["uwsgi", "--ini", "/url-feed/uwsgi/uwsgi.ini"]
