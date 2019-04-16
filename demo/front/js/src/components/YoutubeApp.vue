<template>
<div class="youtube-app">
  <div>
    <h3>Search for a YouTube Video</h3>
  </div>
  
  <div class="xiiot-app-desc">
    Look for a video on YouTube with some interesting objects - a&nbsp;city scene, drone footage or a&nbsp;sporting event are all great options. Then, just copy &amp; paste the URL here!
  </div>
  
  <div class="search-box-outer">
    <input type="text" class="search-box" v-model="searchContent"
           placeholder="YouTube url - e.g. www.youtube.com/watch?v=Kt7jjEAWPds">

    <span class="searchIcon" @click="stop()" v-if="status == 'PLAYING'">
      <i class="fa fa-stop"></i>
    </span>
    
    <span class="searchIcon" @click="sendContent()" v-else>
      <i class="fa fa-play"></i>
    </span>
  </div>
  
  <div class="video-player-area" :style="playerAreaStyle">
    <div v-show="status == 'PLAYING'">
      <video ref="player" class="video-js vjs-default-skin" height="400" width="640" controls preload="none">
      </video>
    </div>
    
    <div v-if="status == 'WAITING'">
        <i class="fa fa-spinner fa-spin" style="font-size: 100px;"></i>
    </div>
    
    <div v-if="status == 'STOPPED'">
      Nothing is playing at the moment
    </div>

  </div>
</div>
</template>

<script src="./youtube_app.ts" lang="ts" />

<style lang="less">
  @import "../styles/Colors.less";

.searchIcon {
    position: relative;
    left: -30px;
    cursor: pointer;
}


.search-box{
    width: 640px;
    color: @dark-gray-1;
    font-size: 14px;
    font-weight: normal;
    letter-spacing: 0px;
    line-height: 10px;
    font-weight: 400;
    padding: 10px;
    border-radius: 4px;
    border: solid 1px #dddddd;
}

.search-box::placeholder {
    color: @gray-3;
}

.search-box:focus{
    outline: none;
    border: solid 1px @blue-1;
}

.vjs-error-display{
    display: none;
}

.youtube-app {
    width: 660px;
}

.youtube-app > div {
    margin: 15px 0px;
}

.video-player-area {
    width: 640px;
    height: 400px;
    border: 1px solid #d5dae0;
    border-radius: 0px 0px 0px 0px;
    display: flex;
    justify-content: center;
    align-items: center;
    
    color: #9aa5b5;
    font-size: 14px;
    font-weight: normal;
    letter-spacing: 0px;
}

</style>
