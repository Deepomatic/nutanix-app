from flask import Flask, request, jsonify
# from flask_cors import CORS, cross_origin
import stream_controller as sc

# so that we don't run into quotas because of Pafy default key
import pafy
import os
if 'YOUTUBE_API_KEY' in os.environ:
    pafy.set_api_key(os.environ['YOUTUBE_API_KEY'])

#
# Simple curl command to execute seeurl
# curl -v -H "Content-Type: application/json" --request POST --data '{"url": "http://www.google.com"}' http://127.0.0.1:5000/seeurl
#


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # To allow CORS ajax calls
    # app.config['CORS_HEADERS'] = 'Content-Type'
    # app.config['CORS_RESOURCES'] = {r"/*": {"origins": "*"}}
    # cors = CORS(app)

    controller = sc.StreamController()

    @app.route('/seeurl', methods=['POST'])
    def see_URL():
        url = request.get_json().get('url')
        print('Start seeing url: ', url)
        controller.start_inference(url)
        thumb_url = controller.metadata(url)['thumb_url']
        status = {'success': True, 'thumb_url': thumb_url}
        return jsonify(status)

    @app.errorhandler(500)
    def internal_error(error):
        return str(error), 500

    return app
