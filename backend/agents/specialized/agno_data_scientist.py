"""
Data Scientist Agent

The Data Scientist agent performs statistical analysis, builds predictive models,
explores data, and provides insights to support business decisions.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID

from backend.agents.agno_base import AgnoSquadAgent, AgentConfig, AgentResponse
from backend.schemas.agent_message import (
    StatusUpdate,
    Question,
    TaskCompletion,
)


class AgnoDataScientistAgent(AgnoSquadAgent):
    """
    Data Scientist Agent (Agno-Powered) - Analytics and Modeling Specialist

    Responsibilities:
    - Perform exploratory data analysis (EDA)
    - Build statistical models
    - Create predictive models
    - Generate insights and recommendations
    - Design experiments and A/B tests
    - Communicate findings to stakeholders
    - Collaborate with data engineers on data pipelines
    - Work with ML engineers on model deployment
    """

    def get_capabilities(self) -> List[str]:
        """
        Return list of Data Scientist capabilities

        Returns:
            List of capability names
        """
        return [
            "exploratory_data_analysis",
            "statistical_analysis",
            "feature_engineering",
            "model_development",
            "model_evaluation",
            "hypothesis_testing",
            "experiment_design",
            "data_visualization",
            "insight_generation",
            "ask_question",
            "provide_status_update",
            "collaborate_with_data_engineer",
            "collaborate_with_ml_engineer",
        ]

    async def exploratory_data_analysis(
        self,
        dataset_description: str,
        data_sources: List[str],
        analysis_goals: Optional[List[str]] = None,
    ) -> AgentResponse:
        """
        Perform exploratory data analysis on a dataset.

        Args:
            dataset_description: Description of the dataset
            data_sources: List of data source locations
            analysis_goals: Optional specific analysis goals

        Returns:
            AgentResponse with EDA findings
        """
        context = {
            "dataset": dataset_description,
            "sources": data_sources,
            "goals": analysis_goals,
            "action": "eda"
        }

        goals_str = ""
        if analysis_goals:
            goals_str = f"""
            Analysis Goals:
            {chr(10).join([f'- {g}' for g in analysis_goals])}
            """

        prompt = f"""
        Perform exploratory data analysis:

        Dataset: {dataset_description}
        Data Sources: {', '.join(data_sources)}
        {goals_str}

        Please provide:

        1. **Data Overview**:
           - Dataset shape and size
           - Column types and distributions
           - Missing values analysis
           - Data quality assessment

        2. **Statistical Summary**:
           - Descriptive statistics
           - Correlation analysis
           - Outlier detection
           - Distribution analysis

        3. **Key Findings**:
           - Interesting patterns
           - Potential issues
           - Data quality concerns
           - Feature relationships

        4. **Visualization Recommendations**:
           - Charts/plots to create
           - What insights they'll reveal

        5. **Next Steps**:
           - Feature engineering opportunities
           - Modeling approaches to consider
           - Additional data needed

        Be thorough and data-driven.
        """

        return await self.process_message(prompt, context=context)

    async def statistical_analysis(
        self,
        research_question: str,
        data_context: str,
        hypothesis: Optional[str] = None,
    ) -> AgentResponse:
        """
        Perform statistical analysis to answer research questions.

        Args:
            research_question: The question to answer
            data_context: Context about available data
            hypothesis: Optional hypothesis to test

        Returns:
            AgentResponse with statistical findings
        """
        context = {
            "question": research_question,
            "data": data_context,
            "hypothesis": hypothesis,
            "action": "statistical_analysis"
        }

        hypothesis_str = ""
        if hypothesis:
            hypothesis_str = f"""
            Hypothesis: {hypothesis}
            """

        prompt = f"""
        Perform statistical analysis:

        Research Question: {research_question}
        Data Context: {data_context}
        {hypothesis_str}

        Please provide:

        1. **Analysis Plan**:
           - Statistical tests to use
           - Assumptions to check
           - Methodology

        2. **Results**:
           - Test statistics
           - P-values
           - Confidence intervals
           - Effect sizes

        3. **Interpretation**:
           - What the results mean
           - Statistical significance
           - Practical significance
           - Limitations

        4. **Recommendations**:
           - Actionable insights
           - Follow-up analyses
           - Additional data needed

        Use appropriate statistical rigor.
        """

        return await self.process_message(prompt, context=context)

    async def feature_engineering(
        self,
        raw_features: List[str],
        target_variable: str,
        problem_type: str,
        data_context: str,
    ) -> AgentResponse:
        """
        Design and engineer features for modeling.

        Args:
            raw_features: List of raw feature names
            target_variable: Target variable name
            problem_type: Classification, regression, etc.
            data_context: Context about the data

        Returns:
            AgentResponse with feature engineering plan
        """
        context = {
            "features": raw_features,
            "target": target_variable,
            "problem_type": problem_type,
            "data": data_context,
            "action": "feature_engineering"
        }

        prompt = f"""
        Design feature engineering strategy:

        Raw Features: {', '.join(raw_features)}
        Target Variable: {target_variable}
        Problem Type: {problem_type}
        Data Context: {data_context}

        Please provide:

        1. **Feature Analysis**:
           - Feature importance assessment
           - Missing value handling
           - Outlier treatment
           - Encoding strategies

        2. **New Features to Create**:
           - Derived features
           - Interaction features
           - Aggregations
           - Transformations

        3. **Feature Selection**:
           - Features to keep
           - Features to remove
           - Dimensionality reduction options

        4. **Implementation Plan**:
           - Steps to engineer features
           - Tools/libraries to use
           - Validation approach

        5. **Expected Impact**:
           - How features will improve model
           - Potential performance gains

        Be creative but practical.
        """

        return await self.process_message(prompt, context=context)

    async def model_development(
        self,
        problem_type: str,
        features: List[str],
        target: str,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        """
        Develop predictive models.

        Args:
            problem_type: Classification, regression, clustering, etc.
            features: List of features to use
            target: Target variable
            constraints: Optional constraints (latency, interpretability, etc.)

        Returns:
            AgentResponse with model development plan
        """
        context = {
            "problem_type": problem_type,
            "features": features,
            "target": target,
            "constraints": constraints,
            "action": "model_development"
        }

        constraints_str = ""
        if constraints:
            constraints_str = f"""
            Constraints:
            {chr(10).join([f'- {k}: {v}' for k, v in constraints.items()])}
            """

        prompt = f"""
        Develop a predictive model:

        Problem Type: {problem_type}
        Features: {', '.join(features)}
        Target: {target}
        {constraints_str}

        Please provide:

        1. **Model Selection**:
           - Candidate models to try
           - Rationale for each
           - Ensemble options

        2. **Training Strategy**:
           - Train/validation/test split
           - Cross-validation approach
           - Hyperparameter tuning plan

        3. **Evaluation Metrics**:
           - Primary metrics
           - Secondary metrics
           - Business metrics

        4. **Implementation Plan**:
           - Libraries/frameworks
           - Code structure
           - Experiment tracking

        5. **Expected Performance**:
           - Baseline expectations
           - Target performance
           - Risk factors

        Focus on practical, deployable models.
        """

        return await self.process_message(prompt, context=context)

    async def model_evaluation(
        self,
        model_results: Dict[str, Any],
        test_metrics: Dict[str, float],
        business_requirements: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        """
        Evaluate model performance and provide recommendations.

        Args:
            model_results: Model training results
            test_metrics: Test set metrics
            business_requirements: Optional business requirements

        Returns:
            AgentResponse with evaluation and recommendations
        """
        context = {
            "results": model_results,
            "metrics": test_metrics,
            "requirements": business_requirements,
            "action": "model_evaluation"
        }

        requirements_str = ""
        if business_requirements:
            requirements_str = f"""
            Business Requirements:
            {chr(10).join([f'- {k}: {v}' for k, v in business_requirements.items()])}
            """

        prompt = f"""
        Evaluate model performance:

        Model Results: {model_results}
        Test Metrics: {test_metrics}
        {requirements_str}

        Please provide:

        1. **Performance Assessment**:
           - How model performs vs. baseline
           - Strengths and weaknesses
           - Metric interpretation

        2. **Business Alignment**:
           - Meets business requirements?
           - ROI considerations
           - Risk assessment

        3. **Model Diagnostics**:
           - Error analysis
           - Bias/variance assessment
           - Overfitting concerns

        4. **Recommendations**:
           - Ready for production?
           - Improvements needed?
           - Alternative approaches?

        5. **Next Steps**:
           - Deployment considerations
           - Monitoring needs
           - Retraining strategy

        Be honest about model limitations.
        """

        return await self.process_message(prompt, context=context)

    async def experiment_design(
        self,
        experiment_goal: str,
        metrics: List[str],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        """
        Design experiments (A/B tests, etc.).

        Args:
            experiment_goal: Goal of the experiment
            metrics: Metrics to measure
            constraints: Optional constraints (sample size, duration, etc.)

        Returns:
            AgentResponse with experiment design
        """
        context = {
            "goal": experiment_goal,
            "metrics": metrics,
            "constraints": constraints,
            "action": "experiment_design"
        }

        constraints_str = ""
        if constraints:
            constraints_str = f"""
            Constraints:
            {chr(10).join([f'- {k}: {v}' for k, v in constraints.items()])}
            """

        prompt = f"""
        Design an experiment:

        Goal: {experiment_goal}
        Metrics: {', '.join(metrics)}
        {constraints_str}

        Please provide:

        1. **Experimental Design**:
           - Hypothesis
           - Control vs. treatment
           - Randomization strategy

        2. **Sample Size Calculation**:
           - Required sample size
           - Power analysis
           - Duration estimate

        3. **Implementation Plan**:
           - How to run experiment
           - Data collection
           - Monitoring approach

        4. **Analysis Plan**:
           - Statistical tests
           - Success criteria
           - Interpretation guidelines

        5. **Risks and Mitigation**:
           - Potential issues
           - How to handle them

        Ensure statistical validity.
        """

        return await self.process_message(prompt, context=context)

    async def insight_generation(
        self,
        analysis_results: Dict[str, Any],
        business_context: str,
        stakeholders: Optional[List[str]] = None,
    ) -> AgentResponse:
        """
        Generate actionable insights from analysis.

        Args:
            analysis_results: Results from analysis
            business_context: Business context
            stakeholders: Optional stakeholder list

        Returns:
            AgentResponse with insights and recommendations
        """
        context = {
            "results": analysis_results,
            "business": business_context,
            "stakeholders": stakeholders,
            "action": "insight_generation"
        }

        prompt = f"""
        Generate insights from analysis:

        Analysis Results: {analysis_results}
        Business Context: {business_context}

        Please provide:

        1. **Key Findings**:
           - Most important discoveries
           - Surprising patterns
           - Confirmed hypotheses

        2. **Business Implications**:
           - What this means for business
           - Opportunities identified
           - Risks highlighted

        3. **Actionable Recommendations**:
           - Specific actions to take
           - Priority ranking
           - Expected impact

        4. **Visualization Suggestions**:
           - Charts to create
           - How to present findings

        5. **Next Steps**:
           - Follow-up analyses
           - Additional data needed
           - Stakeholder communication

        Make insights clear and actionable.
        """

        return await self.process_message(prompt, context=context)

    async def provide_status_update(
        self,
        task_id: str,
        status: str,
        progress_percentage: int,
        findings: Optional[str] = None,
        blockers: Optional[List[str]] = None,
    ) -> StatusUpdate:
        """
        Provide status update to PM or stakeholders.

        Args:
            task_id: Task identifier
            status: Current status
            progress_percentage: Progress (0-100)
            findings: Optional preliminary findings
            blockers: Optional list of blockers

        Returns:
            StatusUpdate message
        """
        return StatusUpdate(
            task_id=task_id,
            status=status,
            progress_percentage=progress_percentage,
            details=findings or "",
            blockers=blockers or [],
            next_steps=None,
        )

