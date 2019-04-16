module.exports = {
    devServer: {
        proxy: {
            '^/url-feed/': {
                target: 'http://localhost:9090'
            },

            '/hls/': {
                target: 'http://localhost:9090'
            }
        }
    }
}
