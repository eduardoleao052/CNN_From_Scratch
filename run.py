import pandas as pd
import numpy as np
from layers import *
from model import Model
from augmenter import Augmenter
from optimizers import *
import logging
import logging.handlers
from argparse import ArgumentParser
import os


def build_logger(sender, pwd, PATH):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s:%(levelname)s: %(message)s")

    file_handler = logging.FileHandler(f"{PATH}/training.log")
    smtpHandler = logging.handlers.SMTPHandler(
    mailhost=("smtp.gmail.com",587),
    fromaddr=sender,
    toaddrs=sender,
    subject="Training Alert",
    credentials=(sender, pwd),
    secure=()
    )

    file_handler.setLevel(logging.INFO)
    smtpHandler.setLevel(logging.WARNING)

    file_handler.setFormatter(formatter)
    smtpHandler.setFormatter(formatter)

    logger.addHandler(smtpHandler)
    logger.addHandler(file_handler)
    return logger

def parse_arguments():
    parser = ArgumentParser(description='configuration of runtime application')
    
    parser.add_argument('--train', action='store_true',
                        help='train the model with provided image dataset')
    parser.add_argument('--test', action='store_true',
                        help='test the model with image dataset')
    
    parser.add_argument('--train_data', nargs='?', type=str, default=f"{PATH}/data/mnist_train.csv",
                        help='path to training dataset used to train model')
    parser.add_argument('--test_data', nargs='?', type=str, default=f"{PATH}/data/mnist_test.csv",
                        help='path to test dataset used to evaluate model')
    parser.add_argument('--epochs',nargs='?', type=int, default=30,
                        help='number of whole passes through training data in training')
    parser.add_argument('--batch_size',nargs='?', type=int, default=15,
                        help='size of the batch (number of images per batch)')
    parser.add_argument('--augmenter_ratio',nargs='?', type=int, default=1,
                        help='1:ratio is how many times the training dataset will be augmented (new images generated by slightly shifting old images)')
    parser.add_argument('--to_path', nargs='?', type=str, default=f"{PATH}/models/model_01.json",
                        help='path to .json file where model will be stored')
    parser.add_argument('--from_path',nargs='?', default=f"{PATH}/models/model_01.json",
                        help='path to file with model parameters to be loaded')
    
    args = parser.parse_args()

    return args

def load_data(args):
    xl = None
    yl = None
    if args.train:
        #Load train data:
        training_data = pd.read_csv(f'{args.train_data}', header=None,low_memory=False)
        yl = training_data.iloc[1:10000,0].astype('float')
        xl = training_data.iloc[1:10000,1:].astype('float')

        #Data Augmentation (shift horizontal & vertical):
        augmenter = Augmenter()
        xl, yl = augmenter.fit_transform(xl,yl,ratio=args.augmenter_ratio)
        
        #Turn into numpy array:
        xl = xl.to_numpy().astype('float')
        yl = yl.to_numpy().astype('float')

        #Normalization:
        xl = (xl - xl.mean()) / (xl.std() + 1e-5)

    #Load test data:
    testing_data = pd.read_csv(f'{args.test_data}', header=None,low_memory=False)
    yt = testing_data.iloc[1:,0].astype('float')
    xt = testing_data.iloc[1:,1:].astype('float')

    #Turn into numpy array:
    xt = xt.to_numpy().astype('float')
    yt = yt.to_numpy().astype('float')

    #Normalization:
    xt = (xt - xt.mean()) / (xt.std() + 1e-5)

    return xl, xt, yl, yt

def train(model):
    #Training Params:
    validation_size = .1
    learning_rate = 1e-3
    regularization = 1e-3
    logger.info("\nTraining model...")
    model.train(xl,yl, epochs = args.epochs, batch_size = args.batch_size, validation_size = validation_size, learning_rate = learning_rate, regularization = regularization) #BEST 5e-4

    test_acc = model.evaluate(model.predict(xt),yt)
    print(test_acc)

    logger.warning("\nTraining complete!\n\nHyperparameters:\nEpochs: {}\nBatch_size: {}\nValidation_size: {}\nlearning_rate: {}\nregularization: {}\n\nStatistics:\nBest Acc Val: {}\nVal Accs: {}\nTest Acc: {}\n\n\n".format(args.epochs,args.batch_size,validation_size,learning_rate,regularization,np.max(model.accs),model.accs,test_acc))
    
    #for i in range(len(model.layers[0].w.T)):
    #            plt.imshow(model.layers[0].w.T[i].reshape(28,28), cmap='hot', interpolation='nearest')
    #            plt.show()
    #            print(i)
    return

def test(model):
    logger.info("\Testing model...")
    #Load model from given path:
    model.load(args.from_path)
    for layer in model.layers:
            layer.compile(0,0)
    model.test(xt,yt)

PATH = os.getcwd()

logger = build_logger('output.logger@gmail.com','bcof jupb ugbh vfll', PATH)
# Get arguments from terminal:
args = parse_arguments()

#Load MNIST data:
logger.info("\nLoading data...")
xl, xt, yl, yt = load_data(args)

#Build Model:
logger.info("\nBuilding model...")
model = Model(logger, args)
model.add(Conv(input_shape = (1,28,28), num_kernels = 3, kernel_size = 5,padding=2))
model.add(BatchNorm())
model.add(Relu())
model.add(MaxPool((3,28,28)))

model.add(Conv(input_shape = (3,14,14), num_kernels = 3, kernel_size = 3, padding=1))
model.add(BatchNorm())
model.add(Relu())
model.add(MaxPool((3,14,14)))

model.add(Flatten((3,7,7)))

model.add(Dense(147,128,optimizer=Adam))
model.add(BatchNorm())
model.add(Relu())
#model.add(Dropout(p=.8))

model.add(Dense(128,128,optimizer=Adam))
model.add(BatchNorm())
model.add(Relu())
#model.add(Dropout(p=.8))

model.add(Dense(128,10,optimizer=Adam))
model.add(Softmax())

#Train or test:
if args.train:
    train(model)
if args.test:
    test(model)