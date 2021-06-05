import os
from flask import Flask
from flask.globals import request
from flask_cors import CORS

import psycopg2

import numpy as np
import string
import json
import regex as re


def preprocessing(text, stop_words):
    text = text.translate(str.maketrans('', '', string.punctuation))
    text = text.lower()
    return [word for word in re.split(" ", text) if word not in stop_words]


def weighted_sentence_embedding(sentence_words, word_freq, model, a):
    sentence_embedding = np.zeros(len(model[list(model.keys())[0]]))
    for word in sentence_words:
        sentence_embedding = np.add(
            sentence_embedding, (a/(a + word_freq[word])) * np.array(model[word]))

    return sentence_embedding


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) + np.linalg.norm(b))


def document_similarity_wr(sentence, document):
    similarities = np.array([cosine_similarity(
        np.array(sentence), np.array(sentence_wr)) for sentence_wr in document])

    # Max similarity
    max = np.max(similarities)

    return max


def mostSimilarDocument_WR(cursor, sentence, articles, a, stop_words):
    cursor.execute("select word, frequence, vector from vocabulary")
    vocabulary = cursor.fetchall()
    word_list = [word[0] for word in vocabulary]
    freq = [word[1] for word in vocabulary]
    vectors = [word[2] for word in vocabulary]

    vocabulary_frequence = dict(zip(word_list, freq))
    vocabulary_vectors = dict(zip(word_list, vectors))

    preproc = preprocessing(sentence, stop_words)
    only_corpus_words = [word for word in preproc if word in word_list]
    sentence_wr = weighted_sentence_embedding(
        only_corpus_words, vocabulary_frequence, vocabulary_vectors, a)

    corpus_wr = []
    for article in range(articles[0], articles[1]):
        cursor.execute(
            "select vector from sentence where article_id = '{0}'".format(article))
        sentences_tuples = cursor.fetchall()
        article_vectors = [sentence_tuple[0]
                           for sentence_tuple in sentences_tuples]
        corpus_wr.append(article_vectors)

    similarities = [document_similarity_wr(
        sentence_wr, doc_wr) for doc_wr in corpus_wr]

    max_indx = similarities.index(max(similarities))

    cursor.execute(
        "select text from articles where id = '{0}'".format(max_indx))
    most_similar_doc = cursor.fetchone()[0]

    doc_name = ''
    if max_indx >= 0 and max_indx <= 148:
        doc_name = 'Regulamento Geral dos Cursos de Graduação'
    elif max_indx >= 149 and max_indx <= 188:
        doc_name = 'Regulamento de Projeto Final de Curso'
    elif max_indx >= 189 and max_indx <= 220:
        doc_name = 'Regulamento de Estágio'

    return doc_name, most_similar_doc


def word_occurences(sentence, corpus_word_freq):
    corpus_occurences = []
    for doc_freq in corpus_word_freq:
        doc_occurences = 0
        for word in sentence:
            if(word in doc_freq):
                doc_occurences += doc_freq[word]

        corpus_occurences.append(doc_occurences)
    return corpus_occurences


def mostSimilarDocument_freq(cursor, sentence, articles, a, stop_words):
    cursor.execute("select word, frequence, vector from vocabulary")
    vocabulary = cursor.fetchall()
    word_list = [word[0] for word in vocabulary]
    freq = [word[1] for word in vocabulary]
    vectors = [word[2] for word in vocabulary]

    vocabulary_frequence = dict(zip(word_list, freq))
    vocabulary_vectors = dict(zip(word_list, vectors))

    preproc = preprocessing(sentence, stop_words)
    only_corpus_words = [word for word in preproc if word in word_list]
    sentence_wr = weighted_sentence_embedding(
        only_corpus_words, vocabulary_frequence, vocabulary_vectors, a)

    corpus_wr = []
    document_word_freq = []
    for article in range(articles[0], articles[1]):
        cursor.execute(
            "select vector from sentence where article_id = '{0}'".format(article))
        sentences_tuples = cursor.fetchall()
        article_vectors = [sentence_tuple[0]
                           for sentence_tuple in sentences_tuples]
        corpus_wr.append(article_vectors)

        cursor.execute(
            "select word, frequence from article_frequence where article_id = '{0}'".format(article))
        frequence_tuples = cursor.fetchall()
        word_freq = [frequence_tuple[0]
                     for frequence_tuple in frequence_tuples]
        value_freq = [frequence_tuple[1]
                      for frequence_tuple in frequence_tuples]
        article_freq = dict(zip(word_freq, value_freq))
        document_word_freq.append(article_freq)

    similarities = np.array([document_similarity_wr(
        sentence_wr, doc_wr) for doc_wr in corpus_wr])

    word_occur = np.array(word_occurences(
        only_corpus_words, document_word_freq))

    similarities = np.add(np.array(similarities), 1e-5 * np.array(word_occur))

    max_indx = np.argmax(similarities)

    cursor.execute(
        "select text from articles where id = '{0}'".format(max_indx))
    most_similar_doc = cursor.fetchone()[0]

    doc_name = ''
    if max_indx >= 0 and max_indx <= 148:
        doc_name = 'Regulamento Geral dos Cursos de Graduação'
    elif max_indx >= 149 and max_indx <= 188:
        doc_name = 'Regulamento de Projeto Final de Curso'
    elif max_indx >= 189 and max_indx <= 220:
        doc_name = 'Regulamento de Estágio'

    return doc_name, most_similar_doc


def tuple_to_dict(tuple):
    parsed = {'id': tuple[0], 'name': tuple[1], 'parent_id': tuple[2]}
    return parsed


def parse_response(response):
    return [tuple_to_dict(element) for element in response]


a = 1e-3

stop_words = ['a', 'o', 'as', 'os', 'qual',
              'quais', 'que', 'de', 'da',
              'do', 'das', 'dos', 'quando',
              'é', 'e', 'na', 'no', 'nas', 'nos', 'para', ]

app = Flask(__name__)
CORS(app)

pg_host = os.environ['PG_HOST']
pg_database = os.environ['PG_DATABASE']
pg_user = os.environ['PG_USER']
pg_port = os.environ['PG_PORT']
pg_password = os.environ['PG_PASSWORD']


@app.route('/', methods=['GET'])
def get_answer():
    question = request.args.get('question')
    topic = request.args.get('topic')

    con = psycopg2.connect(host=pg_host, database=pg_database,
                           user=pg_user, password=pg_password)
    cur = con.cursor()

    if(question is None):
        return json.dumps({'message': 'Question is missing'}), 400

    if(topic == 'estágio'):
        doc_name, most_similar_doc = mostSimilarDocument_WR(
            cur, question, (189, 220), a, stop_words)

        answer = json.dumps({"answer": most_similar_doc})

        return answer

    if(topic == 'projeto_final'):
        doc_name, most_similar_doc = mostSimilarDocument_WR(
            cur, question, (149, 188), a, stop_words)

        answer = json.dumps({"answer": most_similar_doc})

        return answer

    doc_name, most_similar_doc = mostSimilarDocument_freq(
        cur, question, (0, 219), a, stop_words)

    header = 'Segundo o ' + doc_name + ': \n'

    answer = json.dumps({"answer": most_similar_doc, "header": header})

    con.commit()
    con.close()

    return answer


@app.route('/topics', methods=['GET'])
def get_topics():
    con = psycopg2.connect(host='localhost', database='chatbot',
                           user='postgres', password='docker')
    cur = con.cursor()

    sql = "select * from tree where parent_id is null"
    cur.execute(sql)
    response = cur.fetchall()

    con.commit()
    con.close()

    parsed = parse_response(response)

    return json.dumps(parsed)


@app.route('/branches', methods=['GET'])
def get_branches():
    topic_id = request.args.get('id')

    if(topic_id is None):
        return json.dumps({'message': 'Topic id is missing'}), 400

    con = psycopg2.connect(host='localhost', database='chatbot',
                           user='postgres', password='docker')
    cur = con.cursor()

    sql = "select * from tree where parent_id = '%s'" % topic_id
    cur.execute(sql)
    response = cur.fetchall()

    con.commit()
    con.close()

    parsed = parse_response(response)

    return json.dumps(parsed)
