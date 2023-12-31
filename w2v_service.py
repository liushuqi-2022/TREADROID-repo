from flask import Flask
from flask_restful import Api, Resource, reqparse
from gevent import pywsgi
import gensim
import pickle
import os

app = Flask(__name__)
model = gensim.models.KeyedVectors.load_word2vec_format('E:/TREADROID/GoogleNews-vectors-negative300.bin', binary=True)

cached_sim = dict()

if os.path.exists('/w2v_sim_cache.pkl'):
    with open('/w2v_sim_cache.pkl', 'rb') as f:
        cached_sim = pickle.load(f)

@app.route('/')
def w2v_sim(w_from, w_to):
    if (w_from, w_to) in cached_sim:
        return cached_sim[(w_from, w_to)]
    elif (w_to, w_from) in cached_sim:
        return cached_sim[(w_to, w_from)]
    else:
        if w_from.lower() == w_to.lower():
            sim = 1.0
        elif w_from in model.index_to_key and w_to in model.index_to_key:
            sim = model.similarity(w1=w_from, w2=w_to)
        else:
            sim = None
        cached_sim[(w_from, w_to)] = sim
        # with open('/w2v_sim_cache.pkl', 'wb') as f:
            # pickle.dump(cached_sim, f)
        return sim

@app.route('/')
def w2v_sent_sim(s_new, s_old):
    # calculate the similarity score matrix
    scores = []
    valid_new_words = set()
    valid_old_words = set(s_old)
    for w1 in s_new:
        for w2 in valid_old_words:
            sim = w2v_sim(w1, w2)
            if sim:
                valid_new_words.add(w1)
                scores.append((w1, w2, sim))
    scores = sorted(scores, key=lambda x: x[2], reverse=True)
    counted = []
    for new_word, old_word, score in scores:
        if new_word in valid_new_words and old_word in valid_old_words:
            valid_new_words.remove(new_word)
            valid_old_words.remove(old_word)
            counted.append(score)
        if not valid_new_words or not valid_old_words:
            break
    return sum(counted) / len(counted) if counted else None


class WordSim(Resource):
    def get(self):
        return {'error': 'Non-supported HTTP Method'}, 200

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('s_new', action='append')
        parser.add_argument('s_old', action='append')
        args = parser.parse_args()
        sent_sim = w2v_sent_sim(args['s_new'], args['s_old'])
        return {'sent_sim': sent_sim}, 200

    def put(self):
        return {'error': 'Non-supported HTTP Method'}, 200

    def delete(self):
        return {'error': 'Non-supported HTTP Method'}, 200


if __name__ == '__main__':
    
    api = Api(app)
    api.add_resource(WordSim, '/w2v')  # e.g., '/w2v/<string:w1>/<string:w2>'
    app.run(debug=True)
    # app.run(host='0.0.0.0', port=8888, debug = True)
