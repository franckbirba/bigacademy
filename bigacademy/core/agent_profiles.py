#!/usr/bin/env python3
"""
BigAcademy Agent Profiles and Role Definitions
Generic, config-based agent profile system
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path
import yaml
import json

@dataclass
class RoleDefinition:
    """Generic role definition loaded from config"""
    title: str
    description: str
    responsibilities: List[str]
    identity_prompt: str
    communication_style: str
    decision_authority: List[str]
    domain_expertise: List[str]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RoleDefinition':
        """Create role from dictionary"""
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert role to dictionary"""
        return {
            'title': self.title,
            'description': self.description,
            'responsibilities': self.responsibilities,
            'identity_prompt': self.identity_prompt,
            'communication_style': self.communication_style,
            'decision_authority': self.decision_authority,
            'domain_expertise': self.domain_expertise
        }
    
    def get_identity_context(self) -> str:
        """Get role identity for dataset generation"""
        return f"""Role: {self.title}
Description: {self.description}
Identity: {self.identity_prompt}
Communication Style: {self.communication_style}
Expertise: {', '.join(self.domain_expertise)}"""

@dataclass 
class AgentProfile:
    """Generic agent profile loaded from config"""
    name: str
    role: RoleDefinition
    technologies: List[str]
    knowledge_sources: Dict[str, List[str]]
    focus_areas: List[str]
    file_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    knowledge_filters: Dict[str, List[str]] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentProfile':
        """Create profile from dictionary"""
        role = RoleDefinition.from_dict(data['role'])
        return cls(
            name=data['name'],
            role=role,
            technologies=data['technologies'],
            knowledge_sources=data['knowledge_sources'],
            focus_areas=data['focus_areas'],
            file_patterns=data.get('file_patterns', []),
            exclude_patterns=data.get('exclude_patterns', []),
            knowledge_filters=data.get('knowledge_filters', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary"""
        return {
            'name': self.name,
            'role': self.role.to_dict(),
            'technologies': self.technologies,
            'knowledge_sources': self.knowledge_sources,
            'focus_areas': self.focus_areas,
            'file_patterns': self.file_patterns,
            'exclude_patterns': self.exclude_patterns,
            'knowledge_filters': self.knowledge_filters
        }
    
    def matches_technology(self, tech_name: str) -> bool:
        """Check if technology is relevant to this agent"""
        return any(tech.lower() in tech_name.lower() for tech in self.technologies)
    
    def matches_focus_area(self, content: str) -> bool:
        """Check if content matches agent's focus areas"""
        content_lower = content.lower()
        return any(area.lower() in content_lower for area in self.focus_areas)
    
    def get_knowledge_context(self) -> str:
        """Get knowledge context for this agent"""
        return f"""Agent: {self.name}
Technologies: {', '.join(self.technologies)}
Focus Areas: {', '.join(self.focus_areas)}
{self.role.get_identity_context()}"""

class AgentProfileManager:
    """Generic agent profile manager - loads from config files"""
    
    def __init__(self, profiles_dir: Optional[Path] = None):
        self.profiles_dir = profiles_dir or Path("configs/agents")
        self.profiles: Dict[str, AgentProfile] = {}
        self._ensure_profiles_dir()
    
    def _ensure_profiles_dir(self):
        """Ensure profiles directory exists"""
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
    
    def load_all_profiles(self) -> Dict[str, AgentProfile]:
        """Load all agent profiles from config directory"""
        self.profiles.clear()
        
        for profile_file in self.profiles_dir.glob("*.yaml"):
            profile_name = profile_file.stem
            profile = self.load_profile(profile_name)
            if profile:
                self.profiles[profile_name] = profile
        
        return self.profiles
    
    def get_profile(self, name: str) -> Optional[AgentProfile]:
        """Get agent profile by name"""
        if name not in self.profiles:
            self.load_profile(name)
        return self.profiles.get(name)
    
    def list_profiles(self) -> List[str]:
        """List available agent profiles"""
        # Check for new profiles in directory
        available_profiles = [f.stem for f in self.profiles_dir.glob("*.yaml")]
        return sorted(set(list(self.profiles.keys()) + available_profiles))
    
    def create_profile(self, profile: AgentProfile) -> bool:
        """Add and save new agent profile"""
        success = self.save_profile(profile)
        if success:
            self.profiles[profile.name] = profile
        return success
    
    def save_profile(self, profile: AgentProfile) -> bool:
        """Save agent profile to YAML file"""
        try:
            profile_file = self.profiles_dir / f"{profile.name}.yaml"
            profile_data = profile.to_dict()
            
            with open(profile_file, 'w') as f:
                yaml.dump(profile_data, f, default_flow_style=False, allow_unicode=True)
            
            print(f"✅ Saved profile: {profile.name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save profile {profile.name}: {e}")
            return False
    
    def load_profile(self, profile_name: str) -> Optional[AgentProfile]:
        """Load agent profile from YAML file"""
        try:
            profile_file = self.profiles_dir / f"{profile_name}.yaml"
            
            if not profile_file.exists():
                print(f"⚠️  Profile not found: {profile_name}")
                return None
            
            with open(profile_file, 'r') as f:
                data = yaml.safe_load(f)
            
            profile = AgentProfile.from_dict(data)
            self.profiles[profile_name] = profile
            
            print(f"✅ Loaded profile: {profile_name}")
            return profile
            
        except Exception as e:
            print(f"❌ Failed to load profile {profile_name}: {e}")
            return None
    
    def delete_profile(self, profile_name: str) -> bool:
        """Delete agent profile"""
        try:
            profile_file = self.profiles_dir / f"{profile_name}.yaml"
            
            if profile_file.exists():
                profile_file.unlink()
            
            if profile_name in self.profiles:
                del self.profiles[profile_name]
            
            print(f"✅ Deleted profile: {profile_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to delete profile {profile_name}: {e}")
            return False
    
    def validate_profile(self, profile: AgentProfile) -> List[str]:
        """Validate agent profile configuration"""
        errors = []
        
        if not profile.name:
            errors.append("Profile name is required")
        
        if not profile.role.title:
            errors.append("Role title is required")
        
        if not profile.role.identity_prompt:
            errors.append("Role identity prompt is required")
        
        if not profile.technologies:
            errors.append("At least one technology must be specified")
        
        if not profile.focus_areas:
            errors.append("At least one focus area must be specified")
        
        if not profile.knowledge_sources:
            errors.append("Knowledge sources must be specified")
        
        return errors