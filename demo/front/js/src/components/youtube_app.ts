import Vue from 'vue';
import Component from 'vue-class-component';
import axios from 'axios';
import videojs from 'video.js';

type Status = 'STOPPED' | 'WAITING' | 'PLAYING';

function sleep(ms: number) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

type HlsPlayer = videojs.Player & { hls: any };

@Component
export default class YoutubeApp extends Vue {
    searchContent: string = '';

    streamUrl: string = '/hls/stream.m3u8';

    status: Status = 'STOPPED';

    player!: HlsPlayer;

    thumbnailUrl: string = '';

    get playerAreaStyle() {
        if (this.status === 'WAITING' && this.thumbnailUrl !== '') {
            return {
                'background-image': `url("${this.thumbnailUrl}")`,
            };
        } else {
            return {};
        }
    }

    mounted() {
        const options: videojs.PlayerOptions = {
            autoplay: false,
            muted: true,
        };

        this.player = videojs(this.$refs.player, options) as HlsPlayer;

        this.playIfAvailable();
    }

    playIfAvailable() {
        axios.get(this.streamUrl).then(() => {
            this.play(this.streamUrl);
        });
    }

    play(url: string) {
        this.player.reset();
        this.player.src({
            src: url,
            type: 'application/x-mpegURL',
        });

        this.player.play();
        this.status = 'PLAYING';
        console.log('started playing', url);
    }

    stop() {
        this.player.reset();
        this.status = 'STOPPED';
        this.thumbnailUrl = '';
        // FIXME stop the stream on the backend
    }

    sendContent() {
        const url = this.searchContent;

        this.stop();
        this.status = 'WAITING';
        axios.post(`/url-feed/seeurl`, {url}).then(({data}) => {
            if (data.success === true) {
                console.log('post succeeded');
                this.thumbnailUrl = data.thumb_url as string;
                this.status = 'WAITING';
            } else {
                console.log(data);
                this.status = 'STOPPED';
            }
        }).catch((err) => {
            console.error(err);
            console.log('post failed');
            this.status = 'STOPPED';
            return;
        }).then(this.waitForStream);
    }

    waitForStream() {
        let attempt = 0;
        const iv = setInterval(() => {
            if (++attempt > 20) {
                console.log('something went wrong on the backend?');
                this.status = 'STOPPED';
            }
            axios.get(this.streamUrl).then((resp) => {
                console.log(resp);
                clearInterval(iv);
                this.play(this.streamUrl);
            }).catch((e) => {
                this.status = 'WAITING';
            });
        }, 2000);
    }
}

