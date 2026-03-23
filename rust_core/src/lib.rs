use pyo3::prelude::*;
use std::collections::HashSet;

#[pyfunction]
fn fast_keyword_match(user_skills: Vec<String>, job_skills: Vec<String>) -> PyResult<f64> {
    if job_skills.is_empty() {
        return Ok(0.0);
    }
    
    let u_set: HashSet<String> = user_skills
        .into_iter()
        .map(|s| s.to_lowercase().trim().to_string())
        .collect();
    
    let mut matches = 0;
    for s in &job_skills {
        let normalized = s.to_lowercase().trim().to_string();
        if u_set.contains(&normalized) {
            matches += 1;
        }
    }
    
    Ok(matches as f64 / job_skills.len() as f64)
}

#[pyfunction]
fn bulk_score_keywords(user_skills: Vec<String>, jobs_skills: Vec<Vec<String>>) -> PyResult<Vec<f64>> {
    let u_set: HashSet<String> = user_skills
        .into_iter()
        .map(|s| s.to_lowercase().trim().to_string())
        .collect();
    
    let results: Vec<f64> = jobs_skills.into_iter().map(|j_skills| {
        if j_skills.is_empty() {
            return 0.0;
        }
        let mut matches = 0;
        for s in &j_skills {
            let normalized = s.to_lowercase().trim().to_string();
            if u_set.contains(&normalized) {
                matches += 1;
            }
        }
        matches as f64 / j_skills.len() as f64
    }).collect();
    
    Ok(results)
}

/// Compute experience fit score (0-100).
/// Returns 100 if user_exp is within [exp_min, exp_max].
/// Penalizes under- and over-qualification linearly.
#[pyfunction]
fn compute_exp_score(user_exp: f64, exp_min: f64, exp_max: f64) -> PyResult<f64> {
    let max = if exp_max <= 0.0 { exp_min + 2.0 } else { exp_max };
    if user_exp >= exp_min && user_exp <= max {
        return Ok(100.0);
    }
    if user_exp < exp_min {
        let gap = exp_min - user_exp;
        return Ok((100.0 - gap * 22.0).max(0.0).round());
    }
    let gap = user_exp - max;
    Ok((100.0 - gap * 8.0).max(60.0).round())
}

/// Composite tech-fit score combining skill, exp, and location (0-100).
/// Weights: skill=60%, exp=25%, location=15%
#[pyfunction]
fn compute_tech_fit(skill_score: f64, exp_score: f64, location_score: f64) -> PyResult<f64> {
    let fit = 0.60 * skill_score + 0.25 * exp_score + 0.15 * location_score;
    Ok(fit.min(100.0))
}

#[pymodule]
fn career_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fast_keyword_match, m)?)?;
    m.add_function(wrap_pyfunction!(bulk_score_keywords, m)?)?;
    m.add_function(wrap_pyfunction!(compute_exp_score, m)?)?;
    m.add_function(wrap_pyfunction!(compute_tech_fit, m)?)?;
    Ok(())
}
