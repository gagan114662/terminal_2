#!/usr/bin/env python3
"""
Test script for TermNet web search capabilities
Demonstrates browser_search and browser_click_and_collect tools
"""

import asyncio
import sys

# Add the termnet directory to the path
sys.path.insert(0, "termnet/tools")

from browsersearch import BrowserSearchTool


async def test_web_search():
    """Test the web search functionality"""
    tool = BrowserSearchTool()

    print("🔍 Testing TermNet Web Search Capabilities")
    print("=" * 50)

    # Test 1: Search for elements on a news site
    print("\n1. Testing browser_search on news site...")
    try:
        url = "https://news.ycombinator.com"
        results = await tool.search(url, max_results=10)
        print(f"✅ Found {len(results['elements'])} interactive elements")
        print(f"📄 Summary preview: {results['summary'][:200]}...")

        # Show first few elements
        for i, element in enumerate(results["elements"][:3]):
            print(
                f"   {i + 1}. [{element['type']}] {element.get('text', 'N/A')[:50]}..."
            )

    except Exception as e:
        print(f"❌ Error testing news search: {e}")

    # Test 2: Search GitHub for popular repositories
    print("\n2. Testing browser_search on GitHub...")
    try:
        url = "https://github.com/trending"
        results = await tool.search(url, max_results=5)
        print(f"✅ Found {len(results['elements'])} interactive elements")

        # Look for repository links
        repo_links = [
            e
            for e in results["elements"]
            if e["type"] == "link" and "/trending" not in e.get("url", "")
        ]
        print(f"📦 Found {len(repo_links)} repository links")

    except Exception as e:
        print(f"❌ Error testing GitHub search: {e}")

    # Test 3: Click and collect content from a specific page
    print("\n3. Testing browser_click_and_collect...")
    try:
        url = "https://httpbin.org/html"  # Simple test page
        content = await tool.click_and_collect(url)
        print(f"✅ Extracted content ({len(content)} characters)")
        print(f"📄 Content preview: {content[:200]}...")

    except Exception as e:
        print(f"❌ Error testing content extraction: {e}")

    # Test 4: Search for development resources
    print("\n4. Testing search for development resources...")
    try:
        url = "https://developer.mozilla.org/en-US/docs/Web/JavaScript"
        results = await tool.search(url, max_results=8)
        print(f"✅ Found {len(results['elements'])} documentation elements")

        # Count different types of elements
        types = {}
        for element in results["elements"]:
            element_type = element["type"]
            types[element_type] = types.get(element_type, 0) + 1

        print(f"📊 Element types: {types}")

    except Exception as e:
        print(f"❌ Error testing MDN search: {e}")

    print("\n✅ Web search capability testing completed!")
    print("\n🎯 Integration with BMAD workflow:")
    print("- Analyst agent can research competitive products")
    print("- Architect agent can research technology choices")
    print("- Developer agent can search for code examples")
    print("- QA agent can research testing best practices")


async def test_automation_examples():
    """Show examples of different project types for automation testing"""
    print("\n🚀 Examples for Testing Automated BMAD Workflow:")
    print("=" * 55)

    examples = [
        "Create a task management web app with user authentication",
        "Build a REST API for a blog platform with comments",
        "Develop a real-time chat application using WebSockets",
        "Create an e-commerce product catalog with search",
        "Build a personal finance tracker with data visualization",
        "Develop a content management system for small businesses",
        "Create a social media dashboard with analytics",
        "Build a recipe sharing platform with ratings",
        "Develop a project management tool for teams",
        "Create a learning management system with courses",
    ]

    print("Try any of these with automated workflow:")
    for i, example in enumerate(examples, 1):
        print(f"{i:2d}. /analyst {example}")

    print("\n💡 Each command will automatically run all 5 agents:")
    print("   analyst → pm → architect → developer → qa")
    print("\n🌐 The agents will use web search when needed for:")
    print("   - Competitive analysis and market research")
    print("   - Technology stack recommendations")
    print("   - Best practices and industry standards")
    print("   - Code examples and documentation")


if __name__ == "__main__":
    print("🧪 TermNet Web Search & Automation Test Suite")
    print("=" * 50)

    # Run web search tests
    asyncio.run(test_web_search())

    # Show automation examples
    asyncio.run(test_automation_examples())
