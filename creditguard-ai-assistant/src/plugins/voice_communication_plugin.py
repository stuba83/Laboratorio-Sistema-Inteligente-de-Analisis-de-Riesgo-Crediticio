#!/usr/bin/env python3
"""
CreditGuard AI Assistant - Voice Communication Plugin
Instructor: Steven Uba - Azure Digital Solution Engineer - Data and AI
Version: 1.0.0
Purpose: Text-to-speech and voice communication using Azure Speech Services
"""

import asyncio
import json
import aiohttp
import base64
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import logging
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class VoiceProfile:
    """Voice profile configuration"""
    voice_name: str
    language: str
    gender: str
    style: str
    speed: float
    pitch: float
    description: str


@dataclass
class AudioOutput:
    """Audio output information"""
    audio_url: str
    duration_seconds: float
    file_size_bytes: int
    format: str
    voice_used: str
    text_length: int
    generation_timestamp: str


class VoiceCommunicationPlugin:
    """
    Voice Communication Plugin for CreditGuard AI Assistant
    
    Provides text-to-speech capabilities using Azure Speech Services for:
    - Customer notifications (approval/denial)
    - Risk assessment summaries
    - Compliance announcements
    - Multi-language support
    - Professional banking voice styles
    """
    
    def __init__(
        self,
        key: str,
        region: str,
        output_format: str = "audio-24khz-96kbitrate-mono-mp3"
    ):
        self.key = key
        self.region = region
        self.output_format = output_format
        self.logger = logging.getLogger(__name__)
        
        # Azure Speech Service endpoints
        self.tts_endpoint = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
        self.voices_endpoint = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/voices/list"
        
        # Headers for Speech API
        self.headers = {
            'Ocp-Apim-Subscription-Key': self.key,
            'Content-Type': 'application/ssml+xml',
            'X-Microsoft-OutputFormat': self.output_format,
            'User-Agent': 'CreditGuardAI'
        }
        
        # Pre-defined voice profiles for banking context
        self.voice_profiles = {
            'professional_female': VoiceProfile(
                voice_name="en-US-AriaNeural",
                language="en-US",
                gender="Female",
                style="professional",
                speed=0.9,
                pitch=0,
                description="Professional female voice for formal communications"
            ),
            'professional_male': VoiceProfile(
                voice_name="en-US-DavisNeural", 
                language="en-US",
                gender="Male",
                style="professional",
                speed=0.9,
                pitch=0,
                description="Professional male voice for formal communications"
            ),
            'friendly_female': VoiceProfile(
                voice_name="en-US-JennyNeural",
                language="en-US", 
                gender="Female",
                style="friendly",
                speed=1.0,
                pitch=5,
                description="Friendly female voice for customer service"
            ),
            'authoritative_male': VoiceProfile(
                voice_name="en-US-BrandonNeural",
                language="en-US",
                gender="Male", 
                style="serious",
                speed=0.8,
                pitch=-5,
                description="Authoritative male voice for serious communications"
            ),
            'multilingual_spanish': VoiceProfile(
                voice_name="es-US-AlonsoNeural",
                language="es-US",
                gender="Male",
                style="professional",
                speed=0.9,
                pitch=0,
                description="Professional Spanish voice for Hispanic customers"
            )
        }
        
        # Message templates for different scenarios
        self.message_templates = {
            'credit_approved': {
                'professional': "Good news! Your credit application has been approved. You have been granted a credit limit of {limit:,} dollars. Welcome to FinanceFirst Bank. Your new account details will be mailed to you within 5 business days.",
                'friendly': "Congratulations! We're excited to approve your credit application! You've been approved for a {limit:,} dollar credit limit. Welcome to the FinanceFirst family! Keep an eye on your mailbox for your new card details."
            },
            'credit_denied': {
                'professional': "Thank you for your interest in FinanceFirst Bank. Unfortunately, we are unable to approve your credit application at this time. The primary factors in this decision were: {reasons}. You may reapply after addressing these factors.",
                'friendly': "Thank you for considering FinanceFirst Bank. While we can't approve your application right now, this isn't the end of the road. The main areas for improvement are: {reasons}. We'd love to help you in the future once these items are addressed."
            },
            'fraud_alert': {
                'authoritative': "FRAUD ALERT: Suspicious activity has been detected on application number {app_id}. Immediate review required. All processing has been suspended pending investigation. Contact compliance team immediately.",
                'professional': "Security Alert: We've identified some concerns with application {app_id} that require additional verification. Processing has been paused for security purposes. Our team will contact you within 24 hours."
            },
            'compliance_summary': {
                'professional': "Compliance Summary for application {app_id}: All regulatory requirements have been met. FCRA compliance: {fcra_status}. ECOA compliance: {ecoa_status}. Documentation is complete and audit-ready.",
                'authoritative': "Regulatory Compliance Confirmed: Application {app_id} meets all federal requirements. Fair Credit Reporting Act: {fcra_status}. Equal Credit Opportunity Act: {ecoa_status}. Full audit trail established."
            }
        }
        
        # Cache for generated audio
        self._audio_cache = {}
        
        self.logger.info(f"VoiceCommunicationPlugin initialized for region: {region}")
    
    async def text_to_speech(
        self,
        text: str,
        language: str = "en-US",
        voice_style: str = "professional",
        voice_gender: str = "female",
        save_audio: bool = True,
        audio_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convert text to speech using Azure Speech Services
        
        Args:
            text: Text to convert to speech
            language: Language code (e.g., 'en-US', 'es-US')
            voice_style: Voice style ('professional', 'friendly', 'authoritative')
            voice_gender: Voice gender preference ('male', 'female')
            save_audio: Whether to save audio to file
            audio_filename: Custom filename for saved audio
            
        Returns:
            Dictionary containing audio information and URL
        """
        self.logger.info(f"Converting text to speech: {text[:50]}...")
        
        try:
            # Select appropriate voice profile
            voice_profile = self._select_voice_profile(language, voice_style, voice_gender)
            
            # Check cache first
            cache_key = self._generate_cache_key(text, voice_profile.voice_name)
            if cache_key in self._audio_cache:
                self.logger.info("Returning cached audio")
                return self._audio_cache[cache_key]
            
            # Generate SSML
            ssml = self._generate_ssml(text, voice_profile)
            
            # Call Azure Speech API
            audio_data = await self._synthesize_speech(ssml)
            
            # Save audio file if requested
            audio_url = None
            file_size = len(audio_data)
            
            if save_audio:
                audio_url = await self._save_audio_file(
                    audio_data, 
                    audio_filename or f"tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
                )
            
            # Calculate duration (approximate)
            duration = self._estimate_duration(text, voice_profile.speed)
            
            # Create audio output info
            audio_output = AudioOutput(
                audio_url=audio_url or "data:audio/mp3;base64," + base64.b64encode(audio_data).decode(),
                duration_seconds=duration,
                file_size_bytes=file_size,
                format=self.output_format,
                voice_used=voice_profile.voice_name,
                text_length=len(text),
                generation_timestamp=datetime.now().isoformat()
            )
            
            result = asdict(audio_output)
            
            # Cache the result
            self._audio_cache[cache_key] = result
            
            self.logger.info(f"TTS completed: {duration:.1f}s audio, {file_size} bytes")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in text-to-speech: {str(e)}")
            raise
    
    async def generate_credit_decision_announcement(
        self,
        decision_type: str,
        customer_name: str,
        details: Dict[str, Any],
        voice_style: str = "professional",
        language: str = "en-US"
    ) -> Dict[str, Any]:
        """
        Generate voice announcement for credit decisions
        
        Args:
            decision_type: 'approved', 'denied', 'conditional', 'fraud_alert'
            customer_name: Customer's name
            details: Decision details (limit, reasons, etc.)
            voice_style: Voice style preference
            language: Language preference
            
        Returns:
            Audio output information
        """
        self.logger.info(f"Generating {decision_type} announcement for {customer_name}")
        
        try:
            # Generate appropriate message
            message = self._generate_decision_message(decision_type, customer_name, details, voice_style)
            
            # Convert to speech with appropriate voice style
            audio_result = await self.text_to_speech(
                text=message,
                language=language,
                voice_style=voice_style,
                voice_gender="female" if decision_type == "credit_approved" else "male",
                audio_filename=f"{decision_type}_{customer_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
            )
            
            # Add decision-specific metadata
            audio_result['decision_type'] = decision_type
            audio_result['customer_name'] = customer_name
            audio_result['message_template'] = voice_style
            
            return audio_result
            
        except Exception as e:
            self.logger.error(f"Error generating decision announcement: {str(e)}")
            raise
    
    async def generate_compliance_summary(
        self,
        application_id: str,
        compliance_data: Dict[str, Any],
        voice_style: str = "authoritative",
        language: str = "en-US"
    ) -> Dict[str, Any]:
        """
        Generate voice summary of compliance review
        
        Args:
            application_id: Application identifier
            compliance_data: Compliance review results
            voice_style: Voice style preference
            language: Language preference
            
        Returns:
            Audio output information
        """
        self.logger.info(f"Generating compliance summary for {application_id}")
        
        try:
            # Format compliance data for voice
            formatted_data = {
                'app_id': application_id,
                'fcra_status': compliance_data.get('regulatory_checks', {}).get('fcra_compliance', {}).get('status', 'UNKNOWN'),
                'ecoa_status': compliance_data.get('regulatory_checks', {}).get('ecoa_compliance', {}).get('status', 'UNKNOWN')
            }
            
            # Generate compliance message
            template_key = 'compliance_summary'
            template = self.message_templates[template_key].get(voice_style, 
                      self.message_templates[template_key]['professional'])
            
            message = template.format(**formatted_data)
            
            # Convert to speech
            audio_result = await self.text_to_speech(
                text=message,
                language=language,
                voice_style=voice_style,
                voice_gender="male",  # Authoritative compliance voice
                audio_filename=f"compliance_{application_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
            )
            
            # Add compliance-specific metadata
            audio_result['application_id'] = application_id
            audio_result['compliance_score'] = compliance_data.get('compliance_score', 0)
            
            return audio_result
            
        except Exception as e:
            self.logger.error(f"Error generating compliance summary: {str(e)}")
            raise
    
    async def generate_risk_assessment_summary(
        self,
        customer_id: str,
        risk_data: Dict[str, Any],
        voice_style: str = "professional",
        language: str = "en-US"
    ) -> Dict[str, Any]:
        """
        Generate voice summary of risk assessment
        
        Args:
            customer_id: Customer identifier
            risk_data: Risk evaluation results
            voice_style: Voice style preference
            language: Language preference
            
        Returns:
            Audio output information
        """
        self.logger.info(f"Generating risk summary for {customer_id}")
        
        try:
            # Create risk summary message
            risk_level = risk_data.get('risk_level', 'UNKNOWN')
            risk_score = risk_data.get('overall_risk_score', 0)
            recommendation = risk_data.get('recommendation', 'Further review required')
            
            message = f"""
            Risk Assessment Summary for Customer {customer_id}:
            
            Overall Risk Level: {risk_level}
            Risk Score: {risk_score:.1f} out of 100
            
            Key Risk Factors: {len(risk_data.get('risk_factors', []))} factors identified
            
            Recommendation: {recommendation}
            
            Assessment completed at {datetime.now().strftime('%H:%M on %B %d, %Y')}
            """.strip()
            
            # Convert to speech
            audio_result = await self.text_to_speech(
                text=message,
                language=language,
                voice_style=voice_style,
                voice_gender="female",
                audio_filename=f"risk_summary_{customer_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
            )
            
            # Add risk-specific metadata
            audio_result['customer_id'] = customer_id
            audio_result['risk_level'] = risk_level
            audio_result['risk_score'] = risk_score
            
            return audio_result
            
        except Exception as e:
            self.logger.error(f"Error generating risk assessment summary: {str(e)}")
            raise
    
    async def get_available_voices(self, language: str = None) -> List[Dict[str, Any]]:
        """
        Get list of available voices from Azure Speech Service
        
        Args:
            language: Filter by language (optional)
            
        Returns:
            List of available voice configurations
        """
        self.logger.info(f"Fetching available voices for language: {language}")
        
        try:
            headers = {'Ocp-Apim-Subscription-Key': self.key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.voices_endpoint, headers=headers) as response:
                    if response.status == 200:
                        voices = await response.json()
                        
                        # Filter by language if specified
                        if language:
                            voices = [v for v in voices if v.get('Locale', '').startswith(language)]
                        
                        # Format voice information
                        formatted_voices = []
                        for voice in voices:
                            formatted_voice = {
                                'name': voice.get('ShortName'),
                                'display_name': voice.get('DisplayName'),
                                'locale': voice.get('Locale'),
                                'gender': voice.get('Gender'),
                                'voice_type': voice.get('VoiceType'),
                                'styles': voice.get('StyleList', []),
                                'sample_rate': voice.get('SampleRateHertz')
                            }
                            formatted_voices.append(formatted_voice)
                        
                        self.logger.info(f"Retrieved {len(formatted_voices)} voices")
                        return formatted_voices
                    else:
                        self.logger.error(f"Failed to get voices: HTTP {response.status}")
                        return []
                        
        except Exception as e:
            self.logger.error(f"Error fetching available voices: {str(e)}")
            return []
    
    async def batch_generate_announcements(
        self,
        announcements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple voice announcements in batch
        
        Args:
            announcements: List of announcement configurations
            
        Returns:
            List of audio generation results
        """
        self.logger.info(f"Batch generating {len(announcements)} announcements")
        
        try:
            tasks = []
            
            for announcement in announcements:
                if announcement.get('type') == 'decision':
                    task = self.generate_credit_decision_announcement(
                        decision_type=announcement['decision_type'],
                        customer_name=announcement['customer_name'],
                        details=announcement['details'],
                        voice_style=announcement.get('voice_style', 'professional'),
                        language=announcement.get('language', 'en-US')
                    )
                elif announcement.get('type') == 'compliance':
                    task = self.generate_compliance_summary(
                        application_id=announcement['application_id'],
                        compliance_data=announcement['compliance_data'],
                        voice_style=announcement.get('voice_style', 'authoritative'),
                        language=announcement.get('language', 'en-US')
                    )
                elif announcement.get('type') == 'risk':
                    task = self.generate_risk_assessment_summary(
                        customer_id=announcement['customer_id'],
                        risk_data=announcement['risk_data'],
                        voice_style=announcement.get('voice_style', 'professional'),
                        language=announcement.get('language', 'en-US')
                    )
                else:
                    # Custom text announcement
                    task = self.text_to_speech(
                        text=announcement['text'],
                        language=announcement.get('language', 'en-US'),
                        voice_style=announcement.get('voice_style', 'professional'),
                        voice_gender=announcement.get('voice_gender', 'female')
                    )
                
                tasks.append(task)
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        'success': False,
                        'error': str(result),
                        'announcement_index': i
                    })
                else:
                    result['success'] = True
                    result['announcement_index'] = i
                    processed_results.append(result)
            
            success_count = sum(1 for r in processed_results if r.get('success'))
            self.logger.info(f"Batch generation completed: {success_count}/{len(announcements)} successful")
            
            return processed_results
            
        except Exception as e:
            self.logger.error(f"Error in batch announcement generation: {str(e)}")
            raise
    
    def _select_voice_profile(self, language: str, style: str, gender: str) -> VoiceProfile:
        """Select appropriate voice profile based on requirements"""
        
        # Try to match exact requirements
        profile_key = f"{style}_{gender}"
        
        if profile_key in self.voice_profiles:
            profile = self.voice_profiles[profile_key]
            
            # Check language compatibility
            if profile.language.startswith(language[:2]):
                return profile
        
        # Fallback to language-specific profiles
        if language.startswith('es'):
            return self.voice_profiles['multilingual_spanish']
        
        # Default fallback
        return self.voice_profiles['professional_female']
    
    def _generate_ssml(self, text: str, voice_profile: VoiceProfile) -> str:
        """Generate SSML markup for text-to-speech"""
        
        # Clean and prepare text
        clean_text = self._prepare_text_for_speech(text)
        
        # Build SSML with voice configuration
        ssml = f'''
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{voice_profile.language}">
            <voice name="{voice_profile.voice_name}">
                <prosody rate="{voice_profile.speed}" pitch="{voice_profile.pitch:+d}%">
                    <mstts:express-as style="{voice_profile.style}">
                        {clean_text}
                    </mstts:express-as>
                </prosody>
            </voice>
        </speak>
        '''.strip()
        
        return ssml
    
    async def _synthesize_speech(self, ssml: str) -> bytes:
        """Call Azure Speech API to synthesize speech"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.tts_endpoint,
                    headers=self.headers,
                    data=ssml.encode('utf-8')
                ) as response:
                    
                    if response.status == 200:
                        return await response.read()
                    else:
                        error_text = await response.text()
                        raise Exception(f"Speech synthesis failed: HTTP {response.status} - {error_text}")
                        
        except Exception as e:
            self.logger.error(f"Error in speech synthesis: {str(e)}")
            raise
    
    async def _save_audio_file(self, audio_data: bytes, filename: str) -> str:
        """Save audio data to file and return URL"""
        
        try:
            # Create audio directory if it doesn't exist
            audio_dir = Path("temp") / "audio"
            audio_dir.mkdir(parents=True, exist_ok=True)
            
            # Save audio file
            file_path = audio_dir / filename
            
            with open(file_path, 'wb') as f:
                f.write(audio_data)
            
            # Return file URL (in production, this would be a proper URL)
            return f"file://{file_path.absolute()}"
            
        except Exception as e:
            self.logger.error(f"Error saving audio file: {str(e)}")
            # Return data URL as fallback
            return "data:audio/mp3;base64," + base64.b64encode(audio_data).decode()
    
    def _generate_decision_message(
        self,
        decision_type: str,
        customer_name: str,
        details: Dict[str, Any],
        voice_style: str
    ) -> str:
        """Generate appropriate message for credit decision"""
        
        # Map decision types to template keys
        template_mapping = {
            'approved': 'credit_approved',
            'denied': 'credit_denied', 
            'fraud_alert': 'fraud_alert',
            'conditional': 'credit_approved'  # Treat conditional as approved with conditions
        }
        
        template_key = template_mapping.get(decision_type, 'credit_approved')
        
        # Get message template
        templates = self.message_templates[template_key]
        template = templates.get(voice_style, templates.get('professional', templates[list(templates.keys())[0]]))
        
        # Prepare message variables
        message_vars = {
            'customer_name': customer_name,
            'limit': details.get('approved_limit', 0),
            'reasons': ', '.join(details.get('denial_reasons', ['insufficient credit history'])),
            'app_id': details.get('application_id', 'UNKNOWN')
        }
        
        # Generate personalized greeting
        greeting = f"Dear {customer_name}, "
        
        try:
            message = greeting + template.format(**message_vars)
        except KeyError as e:
            self.logger.warning(f"Missing template variable {e}, using fallback")
            message = greeting + f"Thank you for your credit application. Decision: {decision_type.upper()}."
        
        return message
    
    def _prepare_text_for_speech(self, text: str) -> str:
        """Prepare text for speech synthesis"""
        
        # Replace abbreviations with full words
        replacements = {
            'FCRA': 'Fair Credit Reporting Act',
            'ECOA': 'Equal Credit Opportunity Act',
            'SSN': 'Social Security Number',
            'DTI': 'Debt to Income',
            'APR': 'Annual Percentage Rate',
            'ID': 'identification',
            '&': 'and',
            '%': 'percent',
            '$': 'dollar',
            '#': 'number'
        }
        
        for abbrev, full_form in replacements.items():
            text = text.replace(abbrev, full_form)
        
        # Add pauses for better speech flow
        text = text.replace('. ', '. <break time="500ms"/> ')
        text = text.replace('? ', '? <break time="300ms"/> ')
        text = text.replace('! ', '! <break time="400ms"/> ')
        
        # Handle numbers and currencies
        import re
        
        # Format currency
        text = re.sub(r'\$([0-9,]+)', r'\1 dollars', text)
        
        # Format percentages
        text = re.sub(r'([0-9.]+)%', r'\1 percent', text)
        
        return text
    
    def _estimate_duration(self, text: str, speed: float) -> float:
        """Estimate audio duration based on text length and speech rate"""
        
        # Average speech rate: ~150 words per minute
        # Adjust for speed setting
        base_wpm = 150 * speed
        
        # Count words
        word_count = len(text.split())
        
        # Calculate duration in seconds
        duration_minutes = word_count / base_wpm
        duration_seconds = duration_minutes * 60
        
        # Add buffer for pauses and processing
        return duration_seconds * 1.2
    
    def _generate_cache_key(self, text: str, voice_name: str) -> str:
        """Generate cache key for audio content"""
        
        import hashlib
        
        content = f"{text}_{voice_name}_{self.output_format}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def close(self):
        """Clean up plugin resources"""
        
        # Clear audio cache
        self._audio_cache.clear()
        
        # Clean up temporary audio files
        try:
            audio_dir = Path("temp") / "audio"
            if audio_dir.exists():
                for audio_file in audio_dir.glob("*.mp3"):
                    audio_file.unlink()
        except Exception as e:
            self.logger.warning(f"Error cleaning up audio files: {str(e)}")
        
        self.logger.info("VoiceCommunicationPlugin closed")
    
    def __str__(self):
        return f"VoiceCommunicationPlugin(region={self.region}, profiles={len(self.voice_profiles)}, cache_size={len(self._audio_cache)})"