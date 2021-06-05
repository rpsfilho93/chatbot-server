import psycopg2
import json


def stringfyList(array):
    output = '{ '
    for index, element in enumerate(array):
        if(index == len(array) - 1):
            output += str(element) + ' }'
        else:
            output += str(element) + ', '
    return output


con = psycopg2.connect(host='localhost', database='chatbot',
                       user='postgres', password='docker')

cur = con.cursor()

sql = 'drop table if exists tree'
cur.execute(sql)

# Create topics
sql = 'create table tree (id uuid primary key default uuid_generate_v4(), name varchar(256) not null, parent_id uuid, constraint parenting foreign key(parent_id) references tree(id) on delete cascade on update cascade)'
cur.execute(sql)

sql = "insert into tree values (default, 'Atividades Complementares', null)"
cur.execute(sql)

sql = "insert into tree values (default, 'Componentes Curriculares', null)"
cur.execute(sql)

sql = "insert into tree values (default, 'Estágio', null)"
cur.execute(sql)

sql = "insert into tree values (default, 'Projeto Final de Curso', null)"
cur.execute(sql)

# Create Estágio questions
cur.execute("select id from tree where name = 'Estágio'")
estagio_id = cur.fetchone()[0]

sql = "insert into tree values (default, 'O que é necessário para a matrícula na disciplina Estágio Supervisionado?', '%s')" % estagio_id
cur.execute(sql)

sql = "insert into tree values (default, 'O que compete ao estudante estagiário?', '%s')" % estagio_id
cur.execute(sql)

sql = "insert into tree values (default, 'O que é necessário para a conclusão da disciplina Estágio Supervisionado?', '%s')" % estagio_id
cur.execute(sql)

sql = "insert into tree values (default, 'É possível aproveitar as atividades de estágio curricular obrigatório?', '%s')" % estagio_id
cur.execute(sql)

# Create Projeto Final subtopics
cur.execute("select id from tree where name = 'Projeto Final de Curso'")
projeto_id = cur.fetchone()[0]

sql = "insert into tree values (default, 'Plano de Trabalho', '%s')" % projeto_id
cur.execute(sql)

sql = "insert into tree values (default, 'Trabalho Escrito', '%s')" % projeto_id
cur.execute(sql)

sql = "insert into tree values (default, 'Sessão de Defesa', '%s')" % projeto_id
cur.execute(sql)

# Create Plano de Trabalho questions
cur.execute("select id from tree where name = 'Plano de Trabalho'")
plano_id = cur.fetchone()[0]

sql = "insert into tree values (default, 'Quais são os temas permitidos para o Projeto Final?', '%s')" % plano_id
cur.execute(sql)

sql = "insert into tree values (default, 'Qual é o modelo de plano de trabalho do Projeto Final?', '%s')" % plano_id
cur.execute(sql)

sql = "insert into tree values (default, 'Quando deve se  r entregue o plano de trabalho de Projeto Final?', '%s')" % plano_id
cur.execute(sql)

# Create Trabalho Escrito questions
cur.execute("select id from tree where name = 'Trabalho Escrito'")
trabalho_id = cur.fetchone()[0]

sql = "insert into tree values (default, 'Qual é o modelo do trabalho escrito?', '%s')" % trabalho_id
cur.execute(sql)

sql = "insert into tree values (default, 'Como o trabalho escrito deve ser entregue à banca examinadora?', '%s')" % trabalho_id
cur.execute(sql)

# Create Sessão de Defesa questions
cur.execute("select id from tree where name = 'Sessão de Defesa'")
sessao_id = cur.fetchone()[0]

sql = "insert into tree values (default, 'Quantos minutos deve ter a apresentação?', '%s')" % sessao_id
cur.execute(sql)

sql = "insert into tree values (default, 'Como funciona a sessão de questionamentos?', '%s')" % sessao_id
cur.execute(sql)

sql = "insert into tree values (default, 'Como são definidas as datas da defesa?', '%s')" % sessao_id
cur.execute(sql)

# Create Componentes Curriculares questions
cur.execute("select id from tree where name = 'Componentes Curriculares'")
componentes_id = cur.fetchone()[0]

sql = "insert into tree values (default, 'Um componente curricular cursado como NL pode ser aproveitado como NC ou NE?', '%s')" % componentes_id
cur.execute(sql)

sql = "insert into tree values (default, 'Os componentes curriculares cursados antes de ingressar no curso atual, não aproveitados como Núcleo Comum ou Específico, podem ser aproveitados como Núcleo Livre?', '%s')" % componentes_id
cur.execute(sql)

sql = "insert into tree values (default, 'Qual é a porcentagem de carga horária utilizada para a análise de aproveitamento de componente curricular?', '%s')" % componentes_id
cur.execute(sql)

# Create articles table

sql = 'drop table if exists articles'
cur.execute(sql)

sql = 'create table articles (id integer primary key, text varchar(4096) not null)'
cur.execute(sql)

file1 = open('corpus.json',)
articles = json.load(file1)
articles = json.loads(articles)

for index, article in enumerate(articles):
    sql = "insert into articles values('{0}', '{1}' )".format(index, article)
    cur.execute(sql)

sql = 'drop table if exists vocabulary'
cur.execute(sql)

sql = 'create table vocabulary (id serial primary key, word varchar(128) not null, frequence float not null, vector float[] not null)'
cur.execute(sql)

file5 = open('vocabulary_freq_2.json',)
word_freq = json.load(file5)
word_freq = json.loads(word_freq)

file3 = open('vocabulary_vectors_2.json',)
vocab_emb = json.load(file3)
vocab_emb = json.loads(vocab_emb)

for word in word_freq.keys():
    sql = "insert into vocabulary values (default, '{0}', '{1}', '{2}')".format(
          word, word_freq[word], stringfyList(vocab_emb[word]))
    cur.execute(sql)

sql = 'drop table if exists sentence'
cur.execute(sql)

sql = 'create table sentence (id serial primary key, vector float[] not null, article_id integer not null)'
cur.execute(sql)

file4 = open('corpus_emb_2.json',)
corpus_emb = json.load(file4)
corpus_emb = json.loads(corpus_emb)

for index, article in enumerate(corpus_emb):
    for sentence in article:
        sql = "insert into sentence values (default, '{0}', '{1}')".format(
            stringfyList(sentence), index)
        cur.execute(sql)

sql = 'drop table if exists article_frequence'
cur.execute(sql)

sql = 'create table article_frequence (id serial primary key, word varchar(128) not null, frequence float not null, article_id integer not null)'
cur.execute(sql)

file6 = open('corpus_word_frequences.json',)
article_word_freq = json.load(file6)
article_word_freq = json.loads(article_word_freq)

for index, article in enumerate(article_word_freq):
    for word in article.keys():
        sql = "insert into article_frequence values (default, '{0}', '{1}', '{2}')".format(
            word, article[word], index)
        cur.execute(sql)

con.commit()
con.close()
