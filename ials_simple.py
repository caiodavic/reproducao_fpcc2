# coding=utf-8
# Copyright 2024 The Google Research Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# coding=utf-8

r"""Evaluation of iALS following the protocol of the NCF paper.

 - iALS is the algorithm from:
   Hu, Y., Koren, Y., and Volinsky, C.: Collaborative Filtering for Implicit
   Feedback Datasets. ICDM 2008

 - Evaluation follows the protocol from:
   He, X., Liao, L., Zhang, H., Nie, L., Hu, X., and Chua, T.-S.: Neural
   collaborative filtering. WWW 2017
"""

import argparse
# Dataset and evaluation protocols reused from
# https://github.com/hexiangnan/neural_collaborative_filtering
from Dataset import Dataset
from evaluate import evaluate_model
import os
from datetime import datetime

import numpy as np
from collections import defaultdict
from ials import IALS
from ials import DataSet as IALSDataset


class MFModel(IALS):

  def _predict_one(self, user, item):
    """Predicts the score of a user for an item."""
    return np.dot(self.user_embedding[user],
                  self.item_embedding[item])

  def predict(self, pairs, batch_size, verbose):
    """Computes predictions for a given set of user-item pairs.

    Args:
      pairs: A pair of lists (users, items) of the same length.
      batch_size: unused.
      verbose: unused.

    Returns:
      predictions: A list of the same length as users and items, such that
      predictions[i] is the models prediction for (users[i], items[i]).
    """
    del batch_size, verbose
    num_examples = len(pairs[0])
    assert num_examples == len(pairs[1])
    predictions = np.empty(num_examples)
    for i in range(num_examples):
      predictions[i] = self._predict_one(pairs[0][i], pairs[1][i])
    return predictions


def evaluate(model, test_ratings, test_negatives, K=10):
  """Helper that calls evaluate from the NCF libraries."""
  (hits, ndcgs) = evaluate_model(model, test_ratings, test_negatives, K=K,
                                 num_thread=1)
  return np.array(hits).mean(), np.array(ndcgs).mean()

def load_dataset(args):
  dataset = Dataset(args.data)
  train_pos_pairs = np.column_stack(dataset.trainMatrix.nonzero())
  test_ratings, test_negatives = (dataset.testRatings, dataset.testNegatives)
  
  print('Dataset: #user=%d, #item=%d, #train_pairs=%d, #test_pairs=%d' % (
      dataset.num_users, dataset.num_items, train_pos_pairs.shape[0],
      len(test_ratings)))

  
  train_by_user = defaultdict(list)
  train_by_item = defaultdict(list)

  for u, i in train_pos_pairs:
    train_by_user[u].append(i)
    train_by_item[i].append(u)

  train_by_user = list(train_by_user.items())
  train_by_item = list(train_by_item.items())


  return train_by_user, train_by_item, test_ratings, test_negatives, dataset

def make_filename(path, grid_search = False):
  type_data = str(path).split('/')[-1]
  
  list_execs = os.listdir(f'./output/grid_search/{type_data}') if grid_search else os.listdir(f'./output/{type_data}') 
  exec_exps = 1
  
  if len(list_execs) > 0:
    list_execs.sort()  
    exec_exps = int(list_execs[-1].split('_')[1].split('.')[0]) + 1

  if exec_exps < 10:
      filename = f'./output/grid_search/{type_data}/{type_data}_0{exec_exps}.csv' if grid_search else f'./output/{type_data}/{type_data}_0{exec_exps}.csv'
  else:
      filename = f'./output/grid_search/{type_data}/{type_data}_{exec_exps}.csv' if grid_search else f'./output/{type_data}/{type_data}_{exec_exps}.csv'
  
  
  if type_data in ['ml-1m','pinterest-20','last-fm']:
    with open(filename, "w+") as f:
      if grid_search:
        f.write('Epoch,HR@10,NDCG@10,Time,unb_weight,embed_dim,reg\n')
      else:
        f.write('Epoch,HR@10,NDCG@10,Time\n')
  

  if not grid_search:
    print(f'Running iALS on {type_data}. {exec_exps}º execution')
  
  return filename


def train_model(dataset,train_ds, epochs, embedding_dim, regularization, unobserved_weight, stddev, filename, test_ratings, test_negatives,grid_search = False):

  stddev = stddev/np.sqrt(embedding_dim)

  model = MFModel(dataset.num_users, dataset.num_items, embedding_dim, regularization, unobserved_weight, stddev) 

  hr, ndcg = evaluate(model, test_ratings, test_negatives, K=10)

  print(f'Epoch {0}:\t HR={hr:.4f}, NDCG={ndcg:.4f}')
  

  for epoch in range(epochs):
    # Training
    start = datetime.now()
    _ = model.train(train_ds)
    end = datetime.now()
    hr, ndcg_10 = evaluate(model, test_ratings, test_negatives, K=10)
    print(f'Epoch {epoch+1}:\t HR={hr:.4f}, NDCG={ndcg_10:.4f}, Time: {(end-start).total_seconds():.2f}')

    with open(filename, "a") as f:
      if grid_search:
        f.write(f'{epoch+1},{hr},{ndcg_10}, {(end-start).total_seconds()},{unobserved_weight}, {embedding_dim}, {regularization}\n')
      else:
        f.write(f'{epoch+1},{hr},{ndcg_10}, {(end-start).total_seconds()}\n')

  
def main():
  # Command line arguments
  parser = argparse.ArgumentParser()
  parser.add_argument('--data', type=str, default='Data/ml-1m',
                      help='Path to the dataset')
  parser.add_argument('--epochs', type=int, default=128,
                      help='Number of training epochs')
  parser.add_argument('--embedding_dim', type=int, default=8,
                      help='Embedding dimensions, the first dimension will be '
                           'used for the bias.')
  parser.add_argument('--regularization', type=float, default=0.0,
                      help='L2 regularization for user and item embeddings.')
  parser.add_argument('--unobserved_weight', type=float, default=1.0,
                      help='weight for unobserved pairs.')
  parser.add_argument('--stddev', type=float, default=0.1,
                      help='Standard deviation for initialization.')
  parser.add_argument('--grid_search', type=bool, default=False,
                      help='Whether to run grid search.')
  args = parser.parse_args()

  
  
  if args.grid_search:
    unbsorved_weights = [0.1,0.03,0.003]
    embedding_dims = [128,256]
    regularizations = [0.1, 0.03, 0.01, 0.003, 0.001, 0.0003]    

    for unb_weight in unbsorved_weights:
      for embedding_dim in embedding_dims:
        for regularization in regularizations:
          filename = make_filename(args.data, True)
          print(f'Running iALS on {args.data}. Unobserved weight: {unb_weight}, Embedding dim: {embedding_dim}, Regularization: {regularization}')
          train_by_user, train_by_item, test_ratings, test_negatives, dataset = load_dataset(args)
          train_ds = IALSDataset(train_by_user, train_by_item, [], 1)
          _ = train_model(dataset,train_ds, args.epochs, embedding_dim, regularization, unb_weight, args.stddev, filename, test_ratings, test_negatives, True)
    
  else:
    filename = make_filename(args.data, False)
  
    # Load the dataset
  
    train_by_user, train_by_item, test_ratings, test_negatives, dataset = load_dataset(args)
  
    train_ds = IALSDataset(train_by_user, train_by_item, [], 1)
  
    _ = train_model(dataset,train_ds, args.epochs, args.embedding_dim, args.regularization, args.unobserved_weight, args.stddev, filename, test_ratings, test_negatives)
    
if __name__ == '__main__':
  main()
