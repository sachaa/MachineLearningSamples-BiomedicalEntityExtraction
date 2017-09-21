# %%writefile Entity_Extractor.py
from keras.preprocessing import sequence
from keras.models import load_model,save_model
from keras.models import Sequential
from keras.layers import Dense, Input
from keras.layers import LSTM
from keras.layers import GRU
from keras.layers.core import Activation
from keras.regularizers import l2
from keras.layers.wrappers import TimeDistributed
from keras.layers.wrappers import Bidirectional
from keras.layers.normalization import BatchNormalization
from keras.layers import Embedding
from keras.layers.core import Dropout
import numpy as np
import pandas as pd
import sys
import keras.backend as K
from sklearn.metrics import confusion_matrix, classification_report

# For reproducibility
np.random.seed(42)

class EntityExtractor:

    def __init__ (self, reader, embeddings_file_path):
        
        self.reader = reader
        self.model = None
        #self.all_X_train, self.all_Y_train, self.all_X_test, self.all_Y_test, self.wordvecs = \
        #    reader.get_data()

        self.wordvecs = self.reader.load_embedding_lookup_table(embeddings_file_path)

        #self.train_X = self.all_X_train
        #self.train_Y = self.all_Y_train
        
        #self.test_X = self.all_X_test
        #self.test_Y = self.all_Y_test

    def save_tag_map (self, filepath):     
         with open(filepath, 'w') as f:
            for tag in self.reader.tag_to_vector_map.keys():
                try:
                    tag_index = self.reader.tag_to_vector_map[tag].index(1)
                except:
                    continue

                f.write("{}\t{}\n".format(tag, tag_index));

    def load (self, filepath):
        self.model = load_model(filepath)
        
    def save (self, filepath):
        save_model(self.model, filepath, overwrite = True, include_optimizer = True)

    def print_summary (self):
        print(self.model.summary())        
   
    def train (self, train_file, network_type = 'unidirectional', \
               num_epochs = 1, batch_size = 50, dropout = 0.2, reg_alpha = 0.0, \
               num_hidden_units = 150, num_layers = 1):
        
        train_X, train_Y = self.reader.read_and_parse_training_data(train_file)       

        print("Data Shape: ")
        print(train_X.shape)
        print(train_Y.shape)        
        
        dropout = 0.2                
                
        self.model = Sequential()        
        self.model.add(Embedding(self.wordvecs.shape[0], self.wordvecs.shape[1], \
                                 input_length = train_X.shape[1], \
                                 weights = [self.wordvecs], trainable = False))                

        for i in range(0, num_layers):
            if network_type == 'unidirectional':
                # uni-directional LSTM
                self.model.add(LSTM(num_hidden_units, return_sequences = True))
            else:
                # bi-directional LSTM
                self.model.add(Bidirectional(LSTM(num_hidden_units, return_sequences = True)))
        
            self.model.add(Dropout(dropout))

        self.model.add(TimeDistributed(Dense(train_Y.shape[2], activation='softmax')))

        self.model.compile(loss='categorical_crossentropy', optimizer='adam')
        print(self.model.summary())

        self.model.fit(train_X, train_Y, epochs = num_epochs, batch_size = batch_size)
                
    def predict(self, data_frame):
        import json
        from collections import OrderedDict as odict

        feat_vector_list, word_seq_list, num_tokens_list = self.reader.preprocess_unlabeled_data(data_frame)
        print("Data Shape: ")        
        print(feat_vector_list.shape)
        # the output is a list of JSON strings
        predicted_tags= []
        ind = 0
        for feat_vector, word_seq, num_tokens in zip(feat_vector_list, word_seq_list, num_tokens_list):
            prob_dist = self.model.predict(np.array([feat_vector]), batch_size=1)[0]
            pred_tags = self.reader.decode_prediction_sequence(prob_dist)
            pred_dict = odict(zip(word_seq[-num_tokens:], pred_tags[-num_tokens:]))
            pred_str = json.dumps(pred_dict) 
            predicted_tags.append(pred_str)
            ind += 1
            ### To see Progress ###
            if ind % 100 == 0: 
                print("Tagging {} sentences".format(ind))
        
        #predicted_tags = np.array(predicted_tags)
        return predicted_tags
    
    ######################
    # predict_1
    # read the data from the memory
    #####################
    def predict_1(self, data_list):
        import json
        from collections import OrderedDict as odict

        feat_vector_list, word_seq_list, num_tokens_list = self.reader.preprocess_unlabeled_data_1(data_list)
        print("Data Shape: ")        
        print(feat_vector_list.shape)
        # the output is a list of JSON strings
        predicted_tags= []
        ind = 0
        for feat_vector, word_seq, num_tokens in zip(feat_vector_list, word_seq_list, num_tokens_list):
            prob_dist = self.model.predict(np.array([feat_vector]), batch_size=1)[0]
            pred_tags = self.reader.decode_prediction_sequence(prob_dist)
            pred_dict = odict(zip(word_seq[-num_tokens:], pred_tags[-num_tokens:]))
            pred_str = json.dumps(pred_dict) 
            predicted_tags.append(pred_str)
            ind += 1
            ### To see Progress ###
            if ind % 500 == 0: 
               print("Tagging {} sentences".format(ind))
        
        #predicted_tags = np.array(predicted_tags)
        return predicted_tags
    
    ######################
    # predict_2
    # read the data from a file
    #####################
    def predict_2(self, data_file):
        import json
        from collections import OrderedDict as odict

        feat_vector_list, word_seq_list, num_tokens_list = self.reader.preprocess_unlabeled_data_2(data_file)
        print("Data Shape: ")        
        print(feat_vector_list.shape)
        # the output is a list of JSON strings
        predicted_tags= []
        ind = 0
        for feat_vector, word_seq, num_tokens in zip(feat_vector_list, word_seq_list, num_tokens_list):
            prob_dist = self.model.predict(np.array([feat_vector]), batch_size=1)[0]
            pred_tags = self.reader.decode_prediction_sequence(prob_dist)
            pred_dict = odict(zip(word_seq[-num_tokens:], pred_tags[-num_tokens:]))
            pred_str = json.dumps(pred_dict) 
            predicted_tags.append(pred_str)
            ind += 1
            ### To see Progress ###
            if ind % 500 == 0: 
               print("Tagging {} sentences".format(ind))
        
        #predicted_tags = np.array(predicted_tags)
        return predicted_tags
    
    def evaluate_model(self, test_file):
        print("evaluate_model - Begin")
        test_X, test_Y, data_set, num_tokens_list = self.reader.read_and_parse_test_data(test_file)
        
        print("Data Shape: ")        
        print(test_X.shape)
        print(test_Y.shape)
        
        f = open("Pubmed_Output.txt", 'w')
        predicted_tags= []
        target_tags = []
        ind = 0
        #for each line
        for x,y,data_point, num_tokens in zip(test_X, test_Y, data_set, num_tokens_list):
            ind += 1
            ### To see Progress ###
            if ind % 500 == 0: 
                print("processing sentences = " + str(ind))                            

            tags = self.model.predict(np.array([x]), batch_size=1)[0]
            sent_predicted_tags = self.reader.decode_prediction_sequence(tags)
            sent_target_tags = self.reader.decode_prediction_sequence(y)
            
            #remove padding
            sent_predicted_tags = sent_predicted_tags[-num_tokens:]
            sent_target_tags = sent_target_tags[-num_tokens:]

            if len(sent_target_tags) != num_tokens or \
                len(sent_predicted_tags) != num_tokens:
                print("stop here ............")

            for index in range(0, num_tokens):
                target_tag = sent_target_tags[index]
                pred_tag = sent_predicted_tags[index]

                if target_tag != "NONE":
                    if pred_tag == "B-Chemical":
                        predicted_tags.append("B-Drug")
                    elif pred_tag == "I-Chemical":
                        predicted_tags.append("I-Drug")
                    elif pred_tag == 'None':
                        predicted_tags.append('O')
                    else:
                        predicted_tags.append(pred_tag)
                        
                    if target_tag == "B-Chemical":
                        target_tags.append("B-Drug")
                    elif target_tag == "I-Chemical":
                        target_tags.append("I-Drug")
                    else:                        
                        target_tags.append(target_tag)

      
            ##for each token
            for target_tag, predicted_tag, word in zip(sent_target_tags, sent_predicted_tags, list(data_point[0])):
                #f.write(word + '\t' + str(target_tag) + '\t' + str(predicted_tag) + '\n')                                             
                f.write(str(predicted_tag) + '\n')
            f.write("\n")

            #pred_tags_wo_none = []
            #target_tags_wo_none = []            
            ##for each token
            #for index, target_tag in enumerate(target_tags):
            #    if target_tag != "NONE":
            #        if pred_tags[index] == "B-Chemical":
            #            pred_tags_wo_none.append("B-Drug")
            #        elif pred_tags[index] == "I-Chemical":
            #            pred_tags_wo_none.append("I-Drug")
            #        elif pred_tags[index] == 'None':
            #            pred_tags_wo_none.append('O')
            #        else:
            #            pred_tags_wo_none.append(pred_tags[index])
                        
            #        if target_tag == "B-Chemical":
            #            target_tags_wo_none.append("B-Drug")
            #        elif target_tag == "I-Chemical":
            #            target_tags_wo_none.append("I-Drug")
            #        else:                        
            #            target_tags_wo_none.append(target_tag)
            
            #for target_tag, predicted_tag, word in zip(target_tags_wo_none, pred_tags_wo_none, list(data_point[0])):
            #    f.write(word + '\t' + str(target_tag) + '\t' + str(predicted_tag) + '\n')                                             
            #f.write("\n")

            #for i,j in zip(pred_tags, target_tags):
            #    if i != "NONE" and j != "NONE":
            #        target_tags.append(j)
            #        predicted_tags.append(i)       

        f.close()

        predicted_tags = np.array(predicted_tags)
        target_tags = np.array(target_tags)
        print(classification_report(target_tags, predicted_tags))

        simple_conf_matrix = confusion_matrix(target_tags, predicted_tags)
        all_tags = sorted(list(set(target_tags)))
        conf_matrix = pd.DataFrame(columns = all_tags, index = all_tags)
        for x,y in zip(simple_conf_matrix, all_tags):
            conf_matrix[y] = x
        conf_matrix = conf_matrix.transpose()
        
        print("evaluate_model - End")
        return conf_matrix


    def evaluate_1(self):
        target = open("Pubmed_Output.txt", 'w')
        predicted_tags= []
        test_data_tags = []
        ind = 0
        for x,y in zip(self.test_X, self.test_Y):
            tags = self.model.predict(np.array([x]), batch_size=1)[0]
            pred_tags = self.reader.decode_prediction_sequence(tags)
            test_tags = self.reader.decode_prediction_sequence(y)
            ind += 1
            ### To see Progress ###
            if ind%500 == 0: 
                print("Sentence" + str(ind))

            pred_tag_wo_none = []
            test_tags_wo_none = []
            
            for index, test_tag in enumerate(test_tags):
                if test_tag != "NONE":
                    if pred_tags[index] == "B-Chemical":
                        pred_tag_wo_none.append("B-Drug")
                    elif pred_tags[index] == "I-Chemical":
                        pred_tag_wo_none.append("I-Drug")
                    elif pred_tags[index] == 'None':
                        pred_tag_wo_none.append('O')
                    else:
                        pred_tag_wo_none.append(pred_tags[index])
                        
                    if test_tag == "B-Chemical":
                        test_tags_wo_none.append("B-Drug")
                    elif test_tag == "I-Chemical":
                        test_tags_wo_none.append("I-Drug")
                    else:                        
                        test_tags_wo_none.append(test_tag)
            
            for wo in pred_tag_wo_none:
                target.write(str(wo))
                target.write("\n")
            target.write("\n")
            
            for i,j in zip(pred_tags, test_tags):
                if i != "NONE" and j != "NONE":
                    test_data_tags.append(j)
                    predicted_tags.append(i)

        target.close()
        
        predicted_tags = np.array(predicted_tags)
        test_data_tags = np.array(test_data_tags)
        print(classification_report(test_data_tags, predicted_tags))