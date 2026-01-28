import scipy as sp

def proportions_z_test(p1, p2, n1, n2):
    ese=(p1*(1-p1)/n1+p2*(1-p2)/n2)**0.5
    z = (p1-p2)/ese
    # two-sided P-value
    p = sp.stats.norm.sf(abs(z)) * 2
    return p

def check_srm(num_a, num_b, expected_ratio_a=0.5):
    """
    Checks for Sample Ratio Mismatch (SRM) using a Chi-Square test.
    
    Args:
        num_a (int): Number of unique users in Group A.
        num_b (int): Number of unique users in Group B.
        expected_ratio_a (float): The intended split for Group A (e.g., 0.5 for 50/50).
        
    Returns: p-value.
    """
    total_num = num_a + num_b
    # Calculate expected counts based on the total num users
    expected_a = total_num * expected_ratio_a
    expected_b = total_num * (1 - expected_ratio_a)
    observed = [num_a, num_b]
    expected = [expected_a, expected_b]
    
    chi2_stat, p_value = sp.stats.chisquare(f_obs=observed, f_exp=expected)
    
    return p_value
