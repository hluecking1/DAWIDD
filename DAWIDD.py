# -*- coding: utf-8 -*-
import numpy as np
from svm_test import test_independence as svm_independence_test
from kernel_two_sample_test import kernel_two_sample_test
from sklearn.metrics import pairwise_distances
import sys
import os
curr_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.append(curr_folder + "/HSIC")
from HSIC import hsic_gam
import random

def test_independence(X, Y, Z=None):
    return svm_independence_test(X, Y)


class DAWIDD():
    """
    Implementation of the dynamic-adapting-window-independence-drift-detector (DAWIDD)
    
    Parameters
    ----------
    max_window_size : int, optional
        The maximal size of the window. When reaching the maximal size, the oldest sample is removed.

        The default is 90
    min_window_size : int, optional
        The minimal number of samples that is needed for computing the hypothesis test.

        The default is 70
    min_p_value : int, optional
        The threshold of the p-value - not every test outputs a p-value (sometimes only 1.0 <=> independent and 0.0 <=> not independent are returned)

        The default is 0.001
    """
    def __init__(self, X, max_window_size=90, min_window_size=70, min_p_value=0.001):
        self.max_window_size = max_window_size
        self.min_window_size = min_window_size
        self.min_p_value = min_p_value
        self.X_baseline = X
        self.n_items = 0
        self.min_n_items = self.min_window_size / 4.

        self.drift_detected = False
    
    # You have to overwrite this function if you want to use a different test for independence
    def _test_for_independence(self):
        # Tests against random samples from the current baseline and the new incoming data

        # Taking n_items random samples from our baseline dataset which does not include the new data yet
        X = np.array(random.sample(self.X_baseline[:-self.n_items], self.n_items))
        # The data in the current window will be chosen for Y
        Y = np.array(self.X_baseline[-self.n_items:])
        return self.test_independence_hsic(X, Y)
    
    def test_independence_k2st(self, X, Y, alpha=0.005):
        sigma2 = np.median(pairwise_distances(X, Y, metric='euclidean'))**2
        _, _, p_value = kernel_two_sample_test(X, Y, kernel_function='rbf', gamma=1.0/sigma2, verbose=False)

        return True if p_value <= alpha else False

    def test_independence_hsic(self, X, Y, alpha=0.005):
        testStat, _  = hsic_gam(X, Y, alph = 0.05)
        return testStat
    
    def set_input(self, x):
        self.add_batch(x)
        return self.detected_change()

    def add_batch(self, x):
        self.drift_detected = False
        self.X_baseline.append(x.flatten())
        self.n_items += 1
        
        # Is buffer full?
        if self.n_items > self.max_window_size:
            self.X_baseline.pop(0)
            self.n_items -= 1

        # Enough items for testing for drift?
        if self.n_items >= self.min_window_size:
            # Test for drift
            p = self._test_for_independence()

            if p <= self.min_p_value:
                self.drift_detected = True
                
                # Remove samples until no drift is present!
                while p <= self.min_p_value and self.n_items >= self.min_n_items:
                    # Remove old samples
                    self.X_baseline.pop(0)
                    self.n_items -= 1


    def detected_change(self):
        return self.drift_detected
