import numpy as np
from scipy.cluster.vq import kmeans,vq
from scipy.spatial.distance import cdist
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from numpy import genfromtxt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import math
from sklearn.preprocessing import normalize
from xgboost import XGBRegressor
import statistics
from sklearn.ensemble import GradientBoostingRegressor
from create_data_files import create_data_file, create_train_test

fold_path = "data/consolidated/"
result_path = "results/offline/"
def rmsle_func(y_pred, y) : 
	assert len(y) == len(y_pred)
	terms_to_sum = []
	for i,pred in enumerate(y_pred):
		if y_pred[i] <= 0:
			continue
		terms_to_sum.append((math.log(y_pred[i] + 1) - math.log(y[i] + 1)) ** 2.0)
	
	return (sum(terms_to_sum) * (1.0/len(y))) ** 0.5


def load_data(filename):
	data = genfromtxt(filename, delimiter=',')
	return data

def split_into_xy(data):
	x, y = data[:, 1:], data[:, 0]
	return (x, y)

def build_xgboost_model(train_file, max_depth):
	data = load_data(train_file)
	x, y = split_into_xy(data)
	x_normal = normalize(x, norm='l2')
	
	xgb = GradientBoostingRegressor(n_estimators=100, learning_rate=0.20,subsample=0.75,  max_depth=max_depth, loss='quantile')
	model = xgb.fit(x_normal, y)

	return model


def test_model(model, test_file):
	data = load_data(test_file)
	x_test, y_test = split_into_xy(data)
	x_normal = normalize(x_test, norm='l2')
	y_pred = model.predict(x_normal)

	return (y_test, y_pred)



def run_xgboost(train_file, test_file, max_depth):
	model = build_xgboost_model(train_file, max_depth)
	(y_test, y_pred) = test_model(model, test_file)
	rmse = math.sqrt(mean_squared_error(y_test, y_pred))
	rmsle = rmsle_func(y_pred, y_test)
	error_list = []
	for index in range(len(y_test)):
		error_list.append(abs(y_test[index]- y_pred[index]))

	std_dev_error = statistics.stdev(error_list)
	return [rmse, rmsle, std_dev_error]

def run_n_fold_cross_validation(folds, max_depth, result_file_pointer):
	
	total_rmse = 0
	total_rmsle = 0
	total_stddev = 0
	for index in range(folds):
		print "fold = "+str(index)+" starting"
		train_file = fold_path+"train_file_"+str(index)+".txt"
		test_file = fold_path+"train_file_"+str(index)+".txt"
		stat_tuple = run_xgboost(train_file, test_file, max_depth)
		total_rmse = total_rmse + stat_tuple[0]
		total_rmsle = total_rmsle + stat_tuple[1]
		total_stddev = total_stddev + stat_tuple[2]

	avg_rmse = total_rmse/folds
	avg_rmsle = total_rmsle/folds
	avg_stddev = total_stddev/folds

	result_array = []
	result_array.append(max_depth)
	result_array.append(avg_rmse)
	result_array.append(avg_rmsle)
	result_array.append(avg_stddev)
	result_string = ",".join(str(node) for node in result_array) + "\n"
	print result_array
	result_file_pointer.write(result_string)

def run_validation():
	for index in range(7, 9, 1):
		run_n_fold_cross_validation(10, index, result_file_pointer)

def run_algo():
	train_file = "data/train.csv"
	test_file = "data/test.csv"
	data_size = [10000, 50000, 100000, 200000, 500000, 1000000]
	for data in data_size:
		create_train_test(data, False)
		ret_value = run_xgboost(train_file, test_file, 8)
		print ret_value
		file_name = result_path + "quantile_xgboost_"+str(data)+".csv"
		file_pointer = open(file_name, "w+")
		file_pointer.write(str(ret_value))
		file_pointer.close()
if __name__== "__main__":
	run_algo()


