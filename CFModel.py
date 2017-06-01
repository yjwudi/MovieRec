#coding=utf-8
import csv
import numpy as np


class CFModel(object):

	def __init__(self):
		self.load_flag = False
		self.rows = 700
		self.cols = 10500
		self.movie_dic={}#电影id 得到 index
		self.movie_dic_inv = []#index 得到 电影id
		self.user_vec=[[0.0]*self.cols for k in range(self.rows)]

	def load_data(self):
		if(self.load_flag==True):
			return
		self.load_flag = True

		print("read movie id")
		i = 0
		with open('MovieRecommender/importdata/ml-latest-small/movies.csv', 'rb') as f:
			reader = csv.reader(f)
			reader.next()  # skip header
			for row in reader:
				movieId,title,genres = row
				self.movie_dic[movieId] = i
				self.movie_dic_inv.append(movieId)
				i += 1
		print("read over: "+str(i))
		with open('MovieRecommender/importdata/ml-latest-small/ratings.csv', 'rb') as f:
			reader = csv.reader(f)
			reader.next()  # skip header
			for row in reader:
				user_id, movie_id, rating, timestamp = row
				idx = int(self.movie_dic[movie_id])
				self.user_vec[int(user_id)][idx] = float(rating)

	def co_filter_pre(self, movie_list, rating_list):
		user_vec = [0.0]*self.cols
		print(movie_list)
		for i in range(len(movie_list)):
			idx = int(self.movie_dic[str(movie_list[i])])
			print(idx)
			user_vec[idx] = float(rating_list[i])
		return self.co_filter(user_vec)

	def co_filter(self, user_vec):
		self.load_data()
		neighbor = 10
		dist = {}
		x = np.array(user_vec)
		lx = np.sqrt(x.dot(x))
		for i in range(self.rows):
			row = self.user_vec[i]
			if(i>668):
				break
			y = np.array(row)
			v = x.dot(y)
			ly = np.sqrt(y.dot(y))
			dist[i] = v/(lx*ly)
		new_dist = sorted(dist.items(), key=lambda item:item[1], reverse=True)
		#print(new_dist)
		movie_list = []
		for key in new_dist:
			y = self.user_vec[int(key[0])]
			for i in range(len(y)):
				if(y[i]<3.0 or x[i]>0.1):
					continue
				if(self.movie_dic_inv[i] in movie_list):
					continue
				movie_list.append(self.movie_dic_inv[i])
				if(len(movie_list)>=20):
					break
			if(len(movie_list)>=20):
				break
		print("cf movie list:")
		print(movie_list)
		return movie_list






			

	
if __name__ == '__main__':
    cf = CFModel()
    cf.load_data()
    cf.co_filter(cf.user_vec[2])
    #print(cf.user_vec[2])











