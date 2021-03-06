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

    def __init__ (self, reader, embedding_pickle_file=None):
        
        self.reader = reader
        self.model = None       
        
        if not (embedding_pickle_file is None):
            self.wordvecs = self.reader.load_embedding_lookup_table(embedding_pickle_file)
 

    def load (self, filepath):
        self.model = load_model(filepath)
        
    def save (self, filepath):        
        self.model.save(filepath)

    def print_summary (self):
        print(self.model.summary())        
   
    ##################################################
    # train
    ##################################################
    def train (self, train_file, output_resources_pickle_file, \
        network_type = 'unidirectional', \
        num_epochs = 1, batch_size = 50, \
        dropout = 0.2, reg_alpha = 0.0, \
        num_hidden_units = 150, num_layers = 1):
        
        train_X, train_Y = self.reader.read_and_parse_training_data(train_file, output_resources_pickle_file)       

        print("Data Shape: ")
        print(train_X.shape)
        print(train_Y.shape)        
        
        print("Hyper parameters:")
        print("output_resources_pickle_file = {}".format(output_resources_pickle_file))
        print( "network_type = {}".format(network_type))
        print( "num_epochs= {}".format(num_epochs ))
        print("batch_size = {}".format(batch_size ))
        print("dropout = ".format(dropout ))
        print("reg_alpha = {}".format(reg_alpha ))
        print("num_hidden_units = {}".format(num_hidden_units))
        print("num_layers = {}".format(num_layers ))         
                
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

    #########################################
    # predict
    #########################################            
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
    
    #########################################
    # predict_1
    # read the data from the memory
    #########################################
    def predict_1(self, text_list):
        import json
        from collections import OrderedDict as odict

        feat_vector_list, word_seq_list, num_tokens_list = self.reader.get_feature_vectors_1(text_list)
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
    
    ############################################
    # predict_2
    # read the data from a file
    ###########################################
    def predict_2(self, data_file):
        import json
        from collections import OrderedDict as odict

        feat_vector_list, word_seq_list, num_tokens_list = self.reader.get_feature_vectors_2(data_file)
        print("Data Shape: ")        
        print(feat_vector_list.shape)
        # the output is a list of JSON strings
        predicted_tags= []
        ind = 0
        for feat_vector, word_seq, num_tokens in zip(feat_vector_list, word_seq_list, num_tokens_list):
            prob_dist = self.model.predict(np.array([feat_vector]), batch_size=1)[0]
            pred_tags = self.reader.decode_prediction_sequence(prob_dist)
            pred_dict = odict(zip(word_seq, pred_tags[-num_tokens:]))
            pred_str = json.dumps(pred_dict) 
            predicted_tags.append(pred_str)
            ind += 1
            ### To see Progress ###
            if ind % 500 == 0: 
               print("Tagging {} sentences".format(ind))
        
        #predicted_tags = np.array(predicted_tags)
        return predicted_tags
    
    ###########################################
    # evaluate_model
    ###########################################
    def evaluate_model(self, test_file, output_prediction_file):
        print("evaluate_model - Begin")
        test_X, test_Y, data_set, num_tokens_list = self.reader.read_and_parse_test_data(test_file)
        
        print("Data Shape: ")        
        print(test_X.shape)
        print(test_Y.shape)
        
        f = open(output_prediction_file, 'w')
        predicted_tags= []
        target_tags = []
        batch_size = 500
        #for each line        
        for ind in range(0,len(test_X), batch_size):
            batch_test_X = test_X[ind:ind+ batch_size]
            batch_test_Y = test_Y[ind:ind+ batch_size]
            batch_data_set = data_set[ind:ind+ batch_size]
            batch_num_tokens_list = num_tokens_list[ind:ind+ batch_size]             

            #ind += 1
            ### To see Progress ###
            if ind % 500 == 0: 
                print("processing sentences = " + str(ind))                                                   

            batch_class_prob_dist = self.model.predict(np.array(batch_test_X), batch_size=batch_size)
            for class_prob_dist,y,data_point, num_tokens in zip(batch_class_prob_dist, batch_test_Y, batch_data_set, batch_num_tokens_list):
                sent_predicted_tags = self.reader.decode_prediction_sequence(class_prob_dist)
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

        f.close()

        predicted_tags = np.array(predicted_tags)
        target_tags = np.array(target_tags)
        evaluation_report = classification_report(target_tags, predicted_tags)

        all_tags = sorted(list(self.reader.tag_to_vector_map.keys()))
        simple_conf_matrix = confusion_matrix(target_tags, predicted_tags, labels= all_tags)             
        
        conf_matrix_df = pd.DataFrame(data=simple_conf_matrix, columns = all_tags, index = all_tags)  
        
        print("evaluate_model - End")
        return evaluation_report, conf_matrix_df

