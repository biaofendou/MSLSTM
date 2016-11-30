import os
import time
import numpy as np
#import tflearn
import LoadData
import Evaluation
import tensorflow as tf
import matplotlib.pyplot as plt
from keras.layers.recurrent import LSTM, SimpleRNN, GRU
from keras.utils import np_utils
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers import Input, Dense
from keras.layers.recurrent import LSTM, SimpleRNN, GRU
from collections import defaultdict
def batch_vm(v, m):
  shape = tf.shape(v)
  rank = shape.get_shape()[0].value
  v = tf.expand_dims(v, rank)

  vm = tf.mul(v, m)

  return tf.reduce_sum(vm, rank-1)
def batch_vm2(x, m):
  [input_size, output_size] = m.get_shape().as_list()

  input_shape = tf.shape(x)
  batch_rank = input_shape.get_shape()[0].value - 1
  batch_shape = input_shape[:batch_rank]
  output_shape = tf.concat(0, [batch_shape, [output_size]])

  x = tf.reshape(x, [-1, input_size])
  y = tf.matmul(x, m)

  y = tf.reshape(y, output_shape)

  return y

def unpack_sequence(tensor):
    """Split the single tensor of a sequence into a list of frames."""
    return tf.unpack(tf.transpose(tensor, perm=[1, 0, 2]))

def pack_sequence(sequence):
    """Combine a list of the frames into a single tensor of the sequence."""
    return tf.transpose(tf.pack(sequence), perm=[1, 0, 2])

def Model(Label):
    global filepath, filename, sequence_window, number_class, batch_size, hidden_units, input_dim, learning_rate, epoch, is_multi_scale, multi_scale_value, training_level, cross_cv
    result_list_dict = defaultdict(list)
    evaluation_list = ["ACCURACY","F1_SCORE","AUC","G_MEAN"]
    for each in evaluation_list:
        result_list_dict[each] = []

    for tab_cv in range(cross_cv):
        if not tab_cv == 1 :continue

        x_train_multi_list,x_train, y_train, x_testing_multi_list,x_test, y_test = LoadData.GetData(filepath, filename, sequence_window,tab_cv,cross_cv,Multi_Scale=is_multi_scale,Wave_Let_Scale=training_level)
        if training_level < 0:
            pass
        else:
            x_train = x_train_multi_list
            x_test = x_testing_multi_list
        #using Keras to train
        if Label == "Keras":
            np.random.seed(fixed_seed_num)  # for reproducibility
            start = time.clock()
            lstm_object = LSTM(hidden_units, input_length=sequence_window, input_dim=input_dim)
            model = Sequential()
            model.add(lstm_object)  # X.shape is (samples, timesteps, dimension)
            # model.add(LSTM(lstm_size,return_sequences=True,input_shape=(len(X_Training[0]),33)))
            # model.add(LSTM(100,return_sequences=True))
            #model.add(Dense(10, activation="tanh"))
            # model.add(Dense(5,activation="tanh"))
            model.add(Dense(output_dim=number_class))
            #model.add(Activation("sigmoid"))
            model.add(Activation("softmax"))

            # model.compile(optimizer='rmsprop', loss='categorical_crossentropy', metrics=['accuracy'])
            model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

            model.fit(x_train, y_train, batch_size=batch_size, nb_epoch=epoch)

            # result = model.predict(X_Testing, batch_size=batch_size)

            result = model.predict(x_test)

            end = time.clock()
            print("The Time For LSTM is " + str(end - start))
            #print(result)
        elif Label == "TensorFlow":
            tf.reset_default_graph()
            tf.set_random_seed(fixed_seed_num)
            # Network building
            num_neurons = hidden_units

            if training_level > 0:
                number_of_scales = len(x_train_multi_list)
                scale_weight = tf.Variable(tf.random_normal(shape=[number_of_scales]), name="scale_weight")

                if is_multi_scale == True:
                    scale_weight_init_value = [1 / number_of_scales for i in range(number_of_scales)]
                else:
                    scale_weight_init_value = [1, 0, 0, 0, 0]

                scale_weight_init_value = np.array(scale_weight_init_value, dtype='f')
                scale_weight_init = tf.assign(scale_weight, scale_weight_init_value)
                temp_ = tf.constant(1.0, shape=[number_of_scales])

                scale_weight = tf.div(tf.exp(tf.mul(temp_,scale_weight)),tf.gather(tf.cumsum(tf.exp(tf.mul(temp_,scale_weight))),number_of_scales-1))
                #scale_weight = tf.div(tf.mul(temp_, scale_weight),tf.gather(tf.cumsum(tf.mul(temp_, scale_weight)), number_of_scales - 1))


                #output_scale_weight = tf.Print(scale_weight, [scale_weight], message="This is Scale_Weight: ",first_n=1024, summarize=10)

                data_original_train = tf.placeholder(tf.float32,[number_of_scales, 1888, sequence_window, input_dim])

                #data_original_train = tf.placeholder(tf.float32,[1248,number_of_scales, sequence_window, input_dim])
                data_original_train2 = tf.reshape(data_original_train,(number_of_scales, int(data_original_train.get_shape()[1]) * sequence_window * input_dim))

                print("At first this operation is assigned initial weights to each scale level, and this operation only runs once, after it will update...")
                data_for_lstm = tf.reshape(batch_vm2(scale_weight, data_original_train2),(int(data_original_train.get_shape()[1]), sequence_window, input_dim))

                data_for_lstm_multi_scale = data_for_lstm
                """
                #data_for_lstm_multi_scale = data_original_train
                out_put_before_multi_first_level = tf.Print(data_original_train, [tf.gather(tf.gather(tf.gather(data_original_train, 0), 150), 0)],\
                                        message="this is output for first level before multiply weight: ",\
                                        first_n=1024, summarize=10)
                out_put_before_multi_second_level = tf.Print(data_original_train, [tf.gather(tf.gather(tf.gather(data_original_train, 1), 150), 0)],\
                                        message="this is output for second level before multiply weight: ",\
                                        first_n=1024, summarize=10)
                # out_put_before_multi_third_level= tf.Print(data_for_lstm_0, [tf.gather(tf.gather(data_original_train, 2),0)],
                # message="this is output for third level before multiply weight: ")
                out_put_after_multi_level = tf.Print(data_for_lstm_0, [tf.gather(tf.gather(data_for_lstm_0, 150), 0)],\
                                                message="this is output for multi level after multiply weight: ",\
                                                first_n=1024, summarize=10)
                """

            else:
                data_original_train = tf.placeholder(tf.float32, [batch_size,sequence_window,input_dim])
                data_for_lstm_multi_scale = data_original_train

            target = tf.placeholder(tf.float32, [None, number_class])
            lstm_cell = tf.nn.rnn_cell.BasicLSTMCell(num_neurons, forget_bias=1.0, activation=tf.nn.tanh)
            #lstm_cell = tf.nn.rnn_cell.BasicLSTMCell(num_neurons, forget_bias=1.0, activation=tf.nn.tanh)
            #lstm_cell = tf.nn.rnn_cell.GRUCell(num_neurons)

            val, state = tf.nn.dynamic_rnn(lstm_cell, data_for_lstm_multi_scale, dtype=tf.float32)
            output_val_shape = tf.Print(val, [val.get_shape()], message="This is Val Shape: ", first_n=1024,\
                                           summarize=10)

            val = tf.transpose(val, [1, 0, 2])
            last = tf.gather(val, int(val.get_shape()[0]) - 1)

            weight = tf.Variable(tf.truncated_normal([num_neurons, int(target.get_shape()[1])]))
            bias = tf.Variable(tf.constant(0.1, shape=[target.get_shape()[1]]))

            prediction = tf.nn.softmax(tf.matmul(last, weight) + bias)
            output_prediction_shape = tf.Print(last, [last.get_shape()], message="This is last Shape: ", first_n=1024,\
                                           summarize=10)
            #prediction = tf.nn.sigmoid(tf.matmul(last, weight) + bias)
            #output_weight = tf.Print(weight, [weight], message="This is Weight: ")

            cost_cross_entropy = -tf.reduce_sum(target * tf.log(prediction))
            #cost_2 = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(prediction, target, name=None))  # Sigmoid

            optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate)

            minimize = optimizer.minimize(cost_cross_entropy)

            #mistakes = tf.not_equal(tf.argmax(target, 1), tf.argmax(prediction, 1))
            #error = tf.reduce_mean(tf.cast(mistakes, tf.float32))
            correct_pred = tf.equal(tf.argmax(prediction, 1), tf.argmax(target, 1))
            accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))

            init_op = tf.initialize_all_variables()
            sess = tf.Session()

            sess.run(init_op)
            if training_level > 0:
                sess.run(scale_weight_init)
                # saver = tf.train.Saver()
                # saver = tf.train.Saver({"my_interest": scale_weight})
                #scale_weight_init.eval()

            no_of_batches = int(len(y_train) / batch_size)
            epoch_training_loss_list = []
            epoch_val_loss_list = []

            for i in range(epoch):
                ptr = 0
                for j in range(no_of_batches):
                    inp, out = x_train[ptr:ptr + batch_size], y_train[ptr:ptr + batch_size]
                    ptr += batch_size
                    sess.run(minimize, {data_original_train: inp, target: out})
                    training_acc,training_loss = sess.run((accuracy,cost_cross_entropy),{data_original_train: inp, target: out})
                    sess.run(output_val_shape,{data_original_train: inp, target: out})

                    sess.run(output_prediction_shape,{data_original_train: inp, target: out})

                    epoch_training_loss_list.append(training_loss)
                    #sess.run(out_put_before_multi_first_level,{data_original_train: inp, target: out})
                    #sess.run(out_put_before_multi_second_level,{data_original_train: inp, target: out})
                    #sess.run(out_put_before_multi_third_level,{data_original_train: inp, target: out})
                    #sess.run(out_put_after_multi_level,{data_original_train: inp, target: out})

                    #val_acc,val_loss = sess.run((accuracy,cost_cross_entropy),{data_original_train: x_test, target: y_test})
                    #epoch_val_loss_list.append(val_loss)
                    print("Epoch %s"%(str(i))+">"*20+"="+"train_accuracy: %s, train_loss: %s"%(str(training_acc),str(training_loss)))
                      #+",\tval_accuracy: %s, val_loss: %s"%(str(val_acc),str(val_loss)))

            #incorrect = sess.run(error, {data: x_test, target: y_test})

            #result = sess.run(prediction, {data_original_train: x_test, target: y_test})
            print(result)
            print("shape is ("+str(len(result))+","+str(len(result[0]))+')')
            #print('Epoch {:2d} error {:3.1f}%'.format(i + 1, 100 * incorrect))
            if training_level > 0:
                scale_weight = sess.run(scale_weight, {data_original_train: x_test, target: y_test})
                print("The final scale weight is :\n")
                print(scale_weight)
            #save_path = saver.save(sess, os.path.join(os.getcwd(),"modelckpt.txt"))
            #aaa = saver.restore(sess, os.path.join(os.getcwd(),"modelckpt.txt"))
            #all_variables = tf.trainable_variables()
            #var = [v for v in tf.trainable_variables() if v.name == "scale_weight"]
            sess.close()

        results = Evaluation.Evaluation(y_test, result)
        print(results)
        for each_eval, each_result in results.items():
            result_list_dict[each_eval].append(each_result)


    for eachk, eachv in result_list_dict.items():
        result_list_dict[eachk] = np.average(eachv)
    print(result_list_dict)
    with open(os.path.join(os.getcwd(),"TensorFlow_Log"+filename+".txt"),"a")as fout:
        if is_multi_scale:
            outfileline = Label+"_____epoch:"+str(epoch)+",_____learning rate:"+str(learning_rate)+",_____multi_scale:"+str(is_multi_scale)+"\n"
        else:
            outfileline = Label+"_____epoch:"+str(epoch)+",_____learning rate:"+str(learning_rate)+",_____multi_scale:"+str(is_multi_scale)+",_____train_set_using_level:"+str(training_level)+"\n"

        fout.write(outfileline)
        for eachk,eachv in result_list_dict.items():
            fout.write(eachk+": "+str(round(eachv,3))+",\t")
        fout.write('\n')

    return epoch_training_loss_list,epoch_val_loss_list

def epoch_loss_plotting(train_loss_list,val_loss_list):
    num = len(train_loss_list)
    epoch = len(train_loss_list[0])
    x = [i+1 for i in range(epoch)]
    plt.plot(x,train_loss_list[1],'r-',label='multi-scale training loss')
    plt.plot(x,val_loss_list[1],'b-',label='multi-scale val loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid()
    plt.show()

    plt.plot(x, val_loss_list[0], 'r-', label='original val loss')
    plt.plot(x, val_loss_list[1], 'g-', label='multi-scale val loss')
    plt.plot(x, val_loss_list[2], 'b-', label='multi-original val loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.grid()
    plt.legend()
    plt.show()

#Model("Keras")
if __name__=='__main__':
    # Parameters
    global filepath, filename, sequence_window, number_class, batch_size, hidden_units, input_dim, learning_rate, epoch, is_multi_scale, multi_scale_value, training_level, cross_cv
    # ---------------------------Fixed Parameters------------------------------
    filepath = os.getcwd()
    sequence_window = 32
    hidden_units = 200
    input_dim = 33
    number_class = 2
    cross_cv = 2
    fixed_seed_num = 1337
    # -------------------------------------------------------------------------
    filename = 'HB_Slammer.txt'
    learning_rate = 0.05
    epoch = 200
    case_list = [0,1,2]
    multi_scale_value = 5
    batch_size = 1
    #case_list = [0]

    train_loss_list = [[] for i in range(3)]
    val_loss_list = [[] for i in range(3)]
    for each_case in case_list:
        if each_case == 0:
            is_multi_scale = False
            training_level = -1
        elif each_case == 1:
            is_multi_scale = True
            training_level = multi_scale_value
        elif each_case == 2:
            is_multi_scale = False
            training_level = multi_scale_value

        a,b = Model("TensorFlow")
        train_loss_list[each_case].extend(a)
        val_loss_list[each_case].extend(b)

    epoch_loss_plotting(train_loss_list,val_loss_list)