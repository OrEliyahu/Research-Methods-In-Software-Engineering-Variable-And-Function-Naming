from flask import Flask, render_template, request, jsonify
import ast
import os
import pandas as pd
from collections import Counter
import json
import random
import re
import numpy as np


app = Flask(__name__)

def get_questions_ids():
    with open(r"questions_ids.txt", "r") as qustions_file:
        qustions = qustions_file.read().splitlines()
        return [qustion for qustion in qustions if qustion != "" and qustion != "\n"]

def non_empty(l):
    c = 0
    for w in l:
        if w != "":
            c += 1
    return c

def statistics2(file_name):
    with open(file_name) as concepts_file:
        data = ast.literal_eval(concepts_file.read())
        concepts = data[0][1:]
        concepts_words = {}
        concepts_counter = {}
        for i, concept in enumerate(concepts):
            concepts_words[concept] = [l[i + 1] for l in data[1:]]
        for concept in concepts:
            concepts_counter[concept] = dict(Counter(concepts_words[concept]))
        return concepts_counter

def generate_random_answers(data, answers_number):
    selected = random.sample(range(1, len(data)), answers_number)    
    selected_data = [data[0]] + [data[i] for i in selected]
    return selected_data


def count_concepts(data):
    def count_not_empty(lst):
        counter = 0
        for i in range(1, len(lst)):
            if lst[i] != "":
                counter += 1
        return counter
    return [count_not_empty(lst) for lst in data[1:]]


def get_variables_lengths(data):
    lengths = []
    for i in range(1, len(data)):
        lengths += [len(only_ascii(data[i][0]))]
    return lengths


def only_ascii(word):
    return ''.join([c if ord(c) < 256 else ' ' for c in word])


def statistics(file_name_old, file_name_new, question, random_state=False):
    concepts_table_summery = []
    concepts_file_old = open(file_name_old, encoding="utf-8")
    concepts_file_new = open(file_name_new, encoding="utf-8")
    data_old = ast.literal_eval(concepts_file_old.read())
    data_new = ast.literal_eval(concepts_file_new.read())
    
    if random_state:
        if len(data_old) > len(data_new):
            data_old = generate_random_answers(data_old, len(data_new) - 1)
            print(len(data_old))
        elif len(data_old) < len(data_new):
            data_new = generate_random_answers(data_new, len(data_old) - 1)

    concepts_old = data_old[0][1:]
    concepts_new = data_new[0][1:]

    old_lenghts = get_variables_lengths(data_old)
    new_lenghts = get_variables_lengths(data_new)

    concepts_counters_old = {}
    concepts_distribution_old = {}
    for i in range(1, len(data_old[0])):
        concepts_counters_old[data_old[0][i]] = 0
        concepts_distribution_old[data_old[0][i]] = []
        for j in range(1, len(data_old)):
            if data_old[j][i]:
                concepts_counters_old[data_old[0][i]] += 1
                concepts_distribution_old[data_old[0][i]] += [data_old[j][i]]
        concepts_distribution_old[data_old[0][i]] = dict(Counter(concepts_distribution_old[data_old[0][i]]))

    concepts_counters_new = {}
    concepts_distribution_new = {}
    for i in range(1, len(data_new[0])):
        concepts_counters_new[data_new[0][i]] = 0
        concepts_distribution_new[data_new[0][i]] = []
        for j in range(1, len(data_new)):
            if data_new[j][i]:
                concepts_counters_new[data_new[0][i]] += 1
                concepts_distribution_new[data_new[0][i]] += [data_new[j][i]]
        concepts_distribution_new[data_new[0][i]] = dict(Counter(concepts_distribution_new[data_new[0][i]]))

    all_concepts = list(set(concepts_old) | set(concepts_new))
    joint_concepts = list(set(concepts_old) & set(concepts_new))
    concepts_only_old = list(set(concepts_old) - set(concepts_new))
    concepts_only_new = list(set(concepts_new) - set(concepts_old))

    old_concpets_values = [i for i in count_concepts(data_old) if i != 0]
    new_concpets_values = [i for i in count_concepts(data_new) if i != 0]

    

    results = { "number_of_answers_old" : len(data_old) - 1,
    			"number_of_answers_new" : len(data_new) - 1,
    			"all_concepts" : all_concepts,
                "joint_concepts" : joint_concepts,
                "concepts_only_old" : concepts_only_old,
                "concepts_only_new" : concepts_only_new,
                "concepts_counters_old" : concepts_counters_old,
                "concepts_counters_new" : concepts_counters_new,
                "concepts_distribution_old" : concepts_distribution_old,
                "concepts_distribution_new" : concepts_distribution_new,
                "concpets_mean_old" : np.mean(old_concpets_values),
                "concpets_mean_new" : np.mean(new_concpets_values),
                "concpets_var_old" : np.var(old_concpets_values),
                "concpets_var_new" : np.var(new_concpets_values),
                "variables_lengths_mean_old" : np.mean(old_lenghts),
                "variables_lengths_mean_new" : np.mean(new_lenghts),
                "variables_lengths_var_old" : np.var(old_lenghts),
                "variables_lengths_var_new" : np.var(new_lenghts)
    }
    
    
    results_file = open("summaries" + os.sep + question + ".json", "w")
    results_file.write(json.dumps(results, indent=4))
    
    return results


def get_all_words(file_name):
    with open(file_name) as concepts_file:
        data = ast.literal_eval(concepts_file.read())
        words = []
        for i in range(2, len(data)):
            words += data[i][1:]
        words = ["empty" if word == "" else word for word in words]
        return words

def get_answers(questions_id, remove_dups=False, old = False):
    def fix_word(word):        
        return re.sub( '(?<!^)(?=[A-Z][a-z])', '_', word).lower().replace("__", "_")

    filePath =  "results" + os.sep + "results.csv" if not old else "results" + os.sep + "results_old.csv"
    data = pd.read_csv(filePath) 
    questions_ids = get_questions_ids()
    answers = data[questions_id][2:]
    answers = [fix_word(answer) for answer in answers if str(answer) != "nan"]
    if remove_dups:
        answers = list(set(answers))
    return ["variable name"] + answers  

@app.route('/')
def main():
    question = ""
    old = ""
    if request.args.get('old') is None or request.args.get('question') is None:
        question = "Q30"
        old = "0"
    else:
        question = str(request.args.get('question'))
        old = str(request.args.get('old'))
    
    
    old_var = False
    if old == "1":
        old_var = True

    if not os.path.isfile("tables" + os.sep + question + "_" + old + ".txt"):
        answers = get_answers(question, old = old_var)
        idx = [0] * len(answers)
        answers = list([[i, name]] for i, name in zip(idx, answers))
        return render_template("index.html", data = answers, 
                                             questions = get_questions_ids(), 
                                             selected = question, 
                                             old = old)
    
    with open("tables" + os.sep + question + "_" + old +  ".txt", "r", encoding="utf-8") as concepts_file:
        data = ast.literal_eval(concepts_file.read())
    
    return render_template("index.html", data = [list(enumerate(row)) for row in data], 
                                         questions = get_questions_ids(), 
                                         selected = question, 
                                         old = old)

@app.route('/save', methods=['POST'])
def save():	
    try:
        with open("tables" + os.sep + str(request.args.get('q')) + "_" + str(request.args.get('old')) + ".txt", "w", encoding="utf-8") as concepts_file:			
            concepts_file.write(str(request.get_json()))            	
        return "saved"
    except:
        return "failed"

@app.route('/compare2', methods=['GET'])
def compare2():
    question = str(request.args.get('q'))
    old_exist = os.path.isfile("tables" + os.sep + str(request.args.get('q')) + "_1" + ".txt")
    new_exist = os.path.isfile("tables" + os.sep + str(request.args.get('q')) + "_0" + ".txt")
    old_concepts_counter, new_concepts_counter = [], []
    words_for_histogram = {}
    words_for_histogram['old_words'] = []
    words_for_histogram['new_words'] = []

    if not old_exist and not new_exist:
        return "<h1>no data for comparing</h1><br><a href='/?question=" + question + "&old=0'>back</a>"
    
    if old_exist:        
        old_concepts_counter = statistics2("tables" + os.sep + question + "_1.txt")
        words_for_histogram['old_words'] = get_all_words("tables" + os.sep + question + "_1.txt")
    if new_exist:                
        new_concepts_counter = statistics2("tables" + os.sep + question + "_0.txt")        
        words_for_histogram['new_words'] = get_all_words("tables" + os.sep + question + "_0.txt")        

    return render_template("compare2.html", datas = [new_concepts_counter, old_concepts_counter], words = words_for_histogram, q = question)


@app.route('/compare', methods=['GET'])
def compare():
    question = str(request.args.get('q'))
    old_exist = os.path.isfile("tables" + os.sep + str(request.args.get('q')) + "_1" + ".txt")
    new_exist = os.path.isfile("tables" + os.sep + str(request.args.get('q')) + "_0" + ".txt")

    if not old_exist or not new_exist:
        return "<h1>no data for comparing</h1><br><a href='/?question=" + question + "&old=0'>back</a>"
     
    results = statistics("tables" + os.sep + question + "_1.txt", "tables" + os.sep + question + "_0.txt", question)
    return render_template("compare.html", r=results, q=question)


if __name__ == "__main__":
    app.run(debug=True)
