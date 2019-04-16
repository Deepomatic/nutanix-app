import Vue from 'vue';
import Component from 'vue-class-component';
import YoutubeApp from './components/YoutubeApp.vue';

@Component({components: {'youtube-app': YoutubeApp}})
export default class App extends Vue {
}
