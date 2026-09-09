import os
import sys
import duckdb
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agent import Text2SQLWorkflow, Text2SQLGraphNodes, AgentState

def test_semantic_constraint_evaluator_node_categorical_missing():
    nodes = Text2SQLGraphNodes()
    cat = {
        "ecommerce_benchmark": {
            "table_name": "ecommerce_benchmark",
            "columns": [
                {"name": "category", "type": "VARCHAR", "samples": ["Furniture", "Technology"]}
            ]
        }
    }
    state = AgentState(
        question="What are total sales for Furniture in 2024?",
        catalog=cat,
        pruned_catalog=cat,
        execution_success=True,
        clean_sql="SELECT SUM(net_amount) AS total_sales FROM ecommerce_benchmark"
    )
    
    # Should flag missing categorical filter 'Furniture'
    res_state = nodes.semantic_constraint_evaluator_node(state)
    assert res_state.is_valid is False
    assert "Furniture" in res_state.validation_error

def test_semantic_constraint_evaluator_node_date_boundary_missing():
    nodes = Text2SQLGraphNodes()
    cat = {"ecommerce_benchmark": {"table_name": "ecommerce_benchmark", "columns": []}}
    state = AgentState(
        question="how many furniture were sold on the last day of the july month",
        catalog=cat,
        pruned_catalog=cat,
        execution_success=True,
        clean_sql="SELECT SUM(quantity) FROM ecommerce_benchmark WHERE category = 'Furniture'"
    )
    
    # Should flag missing date boundary (LAST_DAY or DAY = 31)
    res_state = nodes.semantic_constraint_evaluator_node(state)
    assert res_state.is_valid is False
    assert "date boundary" in res_state.validation_error.lower()

def test_semantic_constraint_evaluator_node_passing_case():
    nodes = Text2SQLGraphNodes()
    cat = {
        "ecommerce_benchmark": {
            "table_name": "ecommerce_benchmark",
            "columns": [
                {"name": "category", "type": "VARCHAR", "samples": ["Furniture"]}
            ]
        }
    }
    state = AgentState(
        question="What are total sales for Furniture?",
        catalog=cat,
        pruned_catalog=cat,
        execution_success=True,
        clean_sql="SELECT SUM(net_amount) AS total_sales FROM ecommerce_benchmark WHERE UPPER(category) = 'FURNITURE'"
    )
    
    res_state = nodes.semantic_constraint_evaluator_node(state)
    # Filter is present, so evaluation should leave is_valid as True
    assert res_state.execution_success is True
    assert res_state.validation_error == ""
