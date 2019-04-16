<template>
  <div>
    <div class="xiiot-gradient"></div>
    <div class="xiiot-app-header">
      <div><img src="./assets/powered-by-xiiot.png" height="24px"/></div>
      <div>Object Detection</div>
      <div><img src="./assets/nutanix-logo.png" height="12px"/></div>
    </div>

    <div class="xiiot-app">
      <youtube-app></youtube-app>
    </div>
  </div>
</template>

<script src="./app.ts" lang="ts" />

<style lang="less">
 /* copied from prism-reactjs */

 @import "styles/main.less";

 .xiiot-app-header {
     font-size: 28px;
     font-weight: 500;
     height: 80px;
     display: flex;
     flex-direction: row;
     justify-content: space-between;
     padding: 30px 16px 30px 20px;
     box-shadow: 0px 3px 5px #eee;
     color: @dark-gray-3;
     letter-spacing: 0px;
 }

 .xiiot-app-header > div {
     display: flex;
     align-items: center;
 }

 .xiiot-app {
     padding: 30px 0px;
     display: flex;
     justify-content: center;
 }

 .xiiot-app-desc {
     width: 584px;
     height: 44px;
     color: @gray-1;
     font-size: 14px;
     font-weight: normal;
     letter-spacing: 0px;
     line-height: 22px;
 }

 .xiiot-gradient {
     width: 100%;
     height: 8px;
     background: linear-gradient(90deg, #76ce62 0%, #00b5e4 49%, #006bba 100%);
 }

</style>
