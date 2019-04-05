node {
    try {
        load "${DMAKE_JENKINS_FILE}"
        currentBuild.result = 'SUCCESS'
    } catch (e) {
        currentBuild.result = 'FAILURE'
        throw e
    } finally {
    }
}

def notifyBuild(String channel, String buildStatus) {
    if (buildStatus == 'SUCCESS') {
        color = '#36A64F' // green
    } else {
        color = '#D00000' // red
    }
    def message = "${buildStatus}: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})"
    slackSend (color: color, message: message, botUser: true, channel: channel)
}
