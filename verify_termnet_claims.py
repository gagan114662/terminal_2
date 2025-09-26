#!/usr/bin/env python3
"""
Verification script for TermNet claims
Tests all unverified functionality with numeric output
"""

import sys
import os

# Add TermNet paths to system path
sys.path.insert(0, 'TermNet')
sys.path.insert(0, 'TermNet/.bmad-core')

print("=" * 60)
print("TERMNET CLAIMS VERIFICATION")
print("=" * 60)

# 1. Verify AgenticRAG reason_and_retrieve
print("\n1. Testing AgenticRAG reason_and_retrieve:")
print("-" * 40)
try:
    from agentic_rag import AgenticRAG
    rag = AgenticRAG()
    result = rag.reason_and_retrieve('How to create a REST API?')
    if isinstance(result, dict):
        search_results = result.get('search_results', [])
        confidence = result.get('confidence_score', 0.0)
        print(f"results: {len(search_results)}")
        print(f"confidence: {confidence:.2f}")
    else:
        print(f"Unexpected result type: {type(result)}")
except Exception as e:
    print(f"ERROR: {e}")

# 2. Verify RAGProcessor ReAct reasoning steps
print("\n2. Testing RAGProcessor ReAct reasoning:")
print("-" * 40)
try:
    from rag_processor import RAGProcessor
    processor = RAGProcessor()
    result = processor.process_with_react("Explain database connection patterns")
    if isinstance(result, dict):
        steps = result.get('reasoning_steps', [])
        insights = result.get('insights', [])
        print(f"steps: {len(steps)}")
        print(f"insights: {len(insights)}")
    else:
        print(f"Unexpected result type: {type(result)}")
except Exception as e:
    print(f"ERROR: {e}")

# 3. Verify CodeAnalyzer analyze_project
print("\n3. Testing CodeAnalyzer analyze_project:")
print("-" * 40)
try:
    from code_analyzer import CodeAnalyzer
    analyzer = CodeAnalyzer()
    result = analyzer.analyze_project('.')
    if isinstance(result, dict):
        files = result.get('files_analyzed', 0)
        entities = result.get('entities_found', 0)
        print(f"files_analyzed: {files}")
        print(f"entities_found: {entities}")
    else:
        print(f"Unexpected result type: {type(result)}")
except Exception as e:
    print(f"ERROR: {e}")

# 4. Verify Enhanced Orchestrator analyze_and_plan
print("\n4. Testing Enhanced Orchestrator analyze_and_plan:")
print("-" * 40)
try:
    from enhanced_orchestrator import EnhancedOrchestrator
    orchestrator = EnhancedOrchestrator()
    task = "create REST API with database models"
    plan = orchestrator.analyze_and_plan(task)
    if isinstance(plan, dict):
        steps = plan.get('steps', [])
        print(f"plan_steps: {len(steps)}")
        print(f"task: '{task}'")
        if steps:
            print(f"first_step: '{steps[0].get('action', 'N/A')}'")
    else:
        print(f"Unexpected result type: {type(plan)}")
except Exception as e:
    print(f"ERROR: {e}")

# 5. Verify CodeAnalyzer semantic_search
print("\n5. Testing CodeAnalyzer semantic_search:")
print("-" * 40)
try:
    from code_analyzer import CodeAnalyzer
    analyzer = CodeAnalyzer()
    query = "authentication handler"
    results = analyzer.semantic_search(query)
    if isinstance(results, list):
        print(f"Semantic search found {len(results)} hits")
    elif isinstance(results, dict):
        hits = results.get('hits', [])
        print(f"Semantic search found {len(hits)} hits")
    else:
        print(f"Unexpected result type: {type(results)}")
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)