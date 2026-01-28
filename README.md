# E-commerce A\B test

## Projekt description
A E-commerce store wants to add a new Payment Service Provider. The team wants to implement buttons for Apple Pay and Google Pay at the top of the final payment step. With the help of AB test the team checks the efficiency of implementation.

All the data is generated with python and faker.

## Data generation

## Workflow
### 1. Choose metrics and fix hypothesis
- Conversion rate 1 (CR 1) = Unique users with purchase / Unique users with view
- Conversion rate 2 (CR 2) = Unique users with purchase / Unique users with checkout
- ARPU = Total revenue / Unique users with view

I choose CR as the Primary Metric with a 5% MDE because it is more sensitive to the UX changes of a new payment gateway. I kept ARPU as a Secondary  Metric with a 10% MDE to ensure that while I increased conversion, I didn't accidentally lower the total order value

### 2. Choose randomization method and samples parameters
Users were splitted 50-50 randomly. 

### 3. Fix the sample size

Data from metrics_stats.csv
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
Data from experiment_basic_data.csv
| test_group | add_to_basket | checkout | purchase | view  |  cr  | arpu |
|------------|---------------|----------|----------|-------|------|------|
| A          | -         | -     |-     | - | - | - |
| B          | -        | -     | -     | - | - | - |

### 5. Validate the experiment
A/A test 

A/A test passed! 
Can't reject null-hypothesis as P-value test for CR 0.2546.
Samples A and B on history data do not represent significantly difference.

Sample Ratio Mismatch

### 6. Analyse the experiment data and make the decision