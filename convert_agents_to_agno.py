"""
Script to convert BaseSquadAgent agents to AgnoSquadAgent

This script automates the conversion of all specialized agents
from the custom BaseSquadAgent to the Agno-powered AgnoSquadAgent.
"""
import os
from pathlib import Path

def convert_agent_file(input_file: Path, output_file: Path):
    """Convert a single agent file to Agno version"""

    with open(input_file, 'r') as f:
        content = f.read()

    # Replace imports
    content = content.replace(
        'from backend.agents.base_agent import BaseSquadAgent',
        'from backend.agents.agno_base import AgnoSquadAgent'
    )

    # Replace class inheritance
    class_names = [
        'TechLeadAgent',
        'BackendDeveloperAgent',
        'FrontendDeveloperAgent',
        'QATesterAgent',
        'SolutionArchitectAgent',
        'DevOpsEngineerAgent',
        'AIEngineerAgent',
        'DesignerAgent',
    ]

    for class_name in class_names:
        old_declaration = f'class {class_name}(BaseSquadAgent):'
        new_declaration = f'class Agno{class_name}(AgnoSquadAgent):'
        content = content.replace(old_declaration, new_declaration)

    # Update docstrings to mention Agno
    content = content.replace(
        'Agent - ',
        'Agent (Agno-Powered) - '
    )

    # Write output
    with open(output_file, 'w') as f:
        f.write(content)

    print(f"✅ Converted: {input_file.name} -> {output_file.name}")

def main():
    """Convert all agents"""
    agents_dir = Path(__file__).parent / 'backend' / 'agents' / 'specialized'

    agents_to_convert = [
        ('tech_lead.py', 'agno_tech_lead.py'),
        ('backend_developer.py', 'agno_backend_developer.py'),
        ('frontend_developer.py', 'agno_frontend_developer.py'),
        ('qa_tester.py', 'agno_qa_tester.py'),
        ('solution_architect.py', 'agno_solution_architect.py'),
        ('devops_engineer.py', 'agno_devops_engineer.py'),
        ('ai_engineer.py', 'agno_ai_engineer.py'),
        ('designer.py', 'agno_designer.py'),
    ]

    print("\n" + "="*70)
    print("CONVERTING AGENTS TO AGNO")
    print("="*70 + "\n")

    for input_name, output_name in agents_to_convert:
        input_file = agents_dir / input_name
        output_file = agents_dir / output_name

        if input_file.exists():
            try:
                convert_agent_file(input_file, output_file)
            except Exception as e:
                print(f"❌ Error converting {input_name}: {e}")
        else:
            print(f"⚠️  File not found: {input_name}")

    print("\n" + "="*70)
    print("✅ CONVERSION COMPLETE!")
    print("="*70)

if __name__ == "__main__":
    main()
