# E-commerce A\B test

## Projekt description
A E-commerce store wants to add a new Payment Service Provider. The team wants to implement buttons for Apple Pay and Google Pay at the top of the final payment step. With the help of AB test the team checks the efficiency of implementation.

All the data is generated with python and faker.

## Workflow
### 1. Choose metrics and fix hypothesis
- Conversion rate = Unique users with purchase / Unique users with view
- ARPU

We chose CR as the Primary Metric with a 5% MDE because it is more sensitive to the UX changes of a new payment gateway. We kept ARPU as a Secondary  Metric with a 10% MDE to ensure that while we increased conversion, we didn't accidentally lower the total order value

### 2. Choose randomization method and samples parameters 

### 3. Fix the sample size
Sample size n for each (treatment, control) group
 
import numpy as np
import scipy as sp

n = (np.var(control, ddof=1)+np.var(treatment, ddof=1))*((sp.stats.norm.ppf(alpha/2, mu=0, sigma=1)+sp.stats.norm.ppf(beta, mu=0, sigma=1))**2)/(mde**2)

alpha - significance level, probability of error type I
beta - probability of error type II

mde - minimum detectable effect, the smallest improvement or change in metric that an experiment is designed to reliably detect as statistically significant.
Variance(var_history) can be calculated as mean variance for N (N=5) previous months excluding months-outliers 
n = 2*var_history*((sp.stats.norm.ppf(alpha/2, mu=0, sigma=1)+sp.stats.norm.ppf(beta, mu=0, sigma=1))**2)/(mde**2)

### 4. Start the experiment and collect data

### 5. Validate the experiment
A/A test 
Sample Ratio Mismatch

### 6. Analyse the experiment data and make the decision