#!/usr/bin/env python3
"""
BigAcademy Generic Prompt Template Manager
Fully config-based template system with no hardcoded agent types
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import re

@dataclass
class TemplateConfig:
    """Configuration for a prompt template"""
    template_type: str
    description: str
    system_prompt: str
    knowledge_context: str
    task_instruction: str
    response_format: str
    variables: List[str]

class PromptTemplateManager:
    """Generic prompt template manager that works with any agent configuration"""
    
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self.templates: Dict[str, TemplateConfig] = {}
        self.template_types_config = {}
        self._load_all_templates()
    
    def _load_all_templates(self):
        """Load all template configurations from YAML files"""
        # Load template types configuration
        types_file = self.templates_dir / "template_types.yaml"
        if types_file.exists():
            with open(types_file, 'r', encoding='utf-8') as f:
                self.template_types_config = yaml.safe_load(f)
        
        # Load individual template files
        for template_file in self.templates_dir.glob("*.yaml"):
            if template_file.name == "template_types.yaml":
                continue
                
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = yaml.safe_load(f)
                
                template_config = TemplateConfig(
                    template_type=template_data['template_type'],
                    description=template_data['description'],
                    system_prompt=template_data['system_prompt'],
                    knowledge_context=template_data['knowledge_context'],
                    task_instruction=template_data['task_instruction'],
                    response_format=template_data['response_format'],
                    variables=template_data.get('variables', [])
                )
                
                self.templates[template_config.template_type] = template_config
                print(f"✅ Loaded template: {template_config.template_type}")
                
            except Exception as e:
                print(f"❌ Error loading template {template_file}: {e}")
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template types"""
        return list(self.templates.keys())
    
    def get_suitable_templates(self, agent_profile, content_type: str = "code") -> List[str]:
        """Get templates suitable for a specific agent and content type"""
        suitable = []
        
        for template_type, template_config in self.template_types_config.get('template_types', {}).items():
            # Check if template exists
            if template_type not in self.templates:
                continue
            
            # Check if suitable for agent (generic approach)
            suitable_for = template_config.get('suitable_for', ['all_agents'])
            if 'all_agents' in suitable_for:
                suitable.append(template_type)
                continue
            
            # Check against agent's role and focus areas
            agent_role = agent_profile.role.title.lower()
            agent_focus = [area.lower() for area in agent_profile.focus_areas]
            
            for role_pattern in suitable_for:
                if (role_pattern in agent_role or 
                    any(role_pattern in focus for focus in agent_focus)):
                    suitable.append(template_type)
                    break
            
            # Check content type compatibility
            content_types = template_config.get('content_types', ['all'])
            if content_type in content_types or 'all' in content_types:
                if template_type not in suitable:
                    suitable.append(template_type)
        
        return suitable
    
    def generate_prompt(self, template_type: str, agent_profile, knowledge_chunk, 
                       source_info: Dict[str, Any], **kwargs) -> str:
        """Generate a prompt using the specified template and agent/knowledge context"""
        
        if template_type not in self.templates:
            raise ValueError(f"Template type '{template_type}' not found")
        
        template = self.templates[template_type]
        
        # Prepare template variables
        template_vars = self._prepare_template_variables(
            agent_profile, knowledge_chunk, source_info, **kwargs
        )
        
        # Generate each section of the prompt
        sections = []
        
        # System prompt
        if template.system_prompt:
            system_prompt = self._fill_template(template.system_prompt, template_vars)
            sections.append(f"# System Prompt\n{system_prompt}")
        
        # Knowledge context
        if template.knowledge_context:
            knowledge_context = self._fill_template(template.knowledge_context, template_vars)
            sections.append(f"# Knowledge Context\n{knowledge_context}")
        
        # Task instruction
        if template.task_instruction:
            task_instruction = self._fill_template(template.task_instruction, template_vars)
            sections.append(f"# Task\n{task_instruction}")
        
        # Response format
        if template.response_format:
            response_format = self._fill_template(template.response_format, template_vars)
            sections.append(f"# Expected Response Format\n{response_format}")
        
        return "\n\n".join(sections)
    
    def _prepare_template_variables(self, agent_profile, knowledge_chunk, 
                                  source_info: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Prepare all variables needed for template filling"""
        
        # Agent profile variables
        role_vars = {
            'role.title': agent_profile.role.title,
            'role.description': agent_profile.role.description,
            'role.domain_expertise': ', '.join(agent_profile.role.domain_expertise),
            'role.communication_style': agent_profile.role.communication_style,
            'role.identity_prompt': agent_profile.role.identity_prompt
        }
        
        # Agent specific variables
        agent_vars = {
            'technologies': ', '.join(agent_profile.technologies),
            'focus_areas': ', '.join(agent_profile.focus_areas)
        }
        
        # Knowledge chunk variables
        chunk_vars = {
            'chunk.content': knowledge_chunk.content,
            'chunk.source_path': knowledge_chunk.source_path,
            'chunk.file_type': knowledge_chunk.file_type,
            'chunk.language': knowledge_chunk.language or 'text',
            'chunk.relevance_score': knowledge_chunk.relevance_score,
            'chunk.size_tokens': knowledge_chunk.size_tokens
        }
        
        # Source information variables
        source_vars = {
            'source.url': source_info.get('url', 'unknown'),
            'source.type': source_info.get('type', 'unknown')
        }
        
        # Default parameters from config
        default_vars = self.template_types_config.get('default_parameters', {})
        
        # Combine all variables
        template_vars = {
            **role_vars,
            **agent_vars,
            **chunk_vars,
            **source_vars,
            **default_vars,
            **kwargs  # Override with any custom parameters
        }
        
        return template_vars
    
    def _fill_template(self, template_text: str, variables: Dict[str, Any]) -> str:
        """Fill template with variables using safe string formatting"""
        
        # Replace {variable} patterns with actual values
        def replace_var(match):
            var_name = match.group(1)
            return str(variables.get(var_name, f"{{{var_name}}}"))  # Keep unfound variables as-is
        
        # Use regex to find and replace all {variable} patterns
        filled_text = re.sub(r'\{([^}]+)\}', replace_var, template_text)
        
        return filled_text
    
    def get_template_info(self, template_type: str) -> Dict[str, Any]:
        """Get information about a specific template"""
        if template_type not in self.templates:
            return {}
        
        template = self.templates[template_type]
        config_info = self.template_types_config.get('template_types', {}).get(template_type, {})
        
        return {
            'template_type': template.template_type,
            'description': template.description,
            'variables': template.variables,
            'suitable_for': config_info.get('suitable_for', []),
            'content_types': config_info.get('content_types', []),
            'output_format': config_info.get('output_format', 'text')
        }
    
    def validate_template_variables(self, template_type: str, provided_vars: Dict[str, Any]) -> List[str]:
        """Validate that all required variables are provided for a template"""
        if template_type not in self.templates:
            return [f"Template '{template_type}' not found"]
        
        template = self.templates[template_type]
        missing_vars = []
        
        for var in template.variables:
            if var not in provided_vars:
                missing_vars.append(var)
        
        return missing_vars