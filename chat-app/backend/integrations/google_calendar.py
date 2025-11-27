"""
Integração com Google Calendar API para agendamento de reuniões.

Este módulo fornece funcionalidades para:
- Autenticação OAuth2 com Google Calendar
- Criar eventos/reuniões no calendário
- Verificar disponibilidade de horários
- Enviar convites por email
- Atualizar e cancelar eventos

Usado principalmente pelo agente SDR para agendar reuniões com leads.
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Escopos necessários para ler e gerenciar eventos do calendário
SCOPES = ['https://www.googleapis.com/auth/calendar']


class GoogleCalendarService:
    """
    Serviço para interagir com Google Calendar API.
    
    Gerencia autenticação OAuth2 e operações CRUD de eventos.
    """
    
    def __init__(
        self,
        credentials_path: str = "credentials.json",
        token_path: str = "token.json"
    ):
        """
        Inicializa o serviço do Google Calendar.
        
        Args:
            credentials_path: Caminho para o arquivo credentials.json do Google Cloud
            token_path: Caminho para armazenar o token de autenticação
        """
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self.credentials: Optional[Credentials] = None
        self.service = None
        
    def authenticate(self) -> bool:
        """
        Realiza autenticação OAuth2 com Google Calendar.
        
        Returns:
            True se autenticação foi bem sucedida, False caso contrário
        """
        try:
            # Verifica se já existe token válido
            if self.token_path.exists():
                self.credentials = Credentials.from_authorized_user_file(
                    str(self.token_path), SCOPES
                )
            
            # Se não há credenciais válidas, realiza login
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    # Renova token expirado
                    self.credentials.refresh(Request())
                else:
                    # Inicia fluxo OAuth2
                    if not self.credentials_path.exists():
                        raise FileNotFoundError(
                            f"Arquivo credentials.json não encontrado em {self.credentials_path}. "
                            "Baixe-o do Google Cloud Console."
                        )
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path), SCOPES
                    )
                    self.credentials = flow.run_local_server(port=0)
                
                # Salva o token para próximas execuções
                with open(self.token_path, 'w') as token:
                    token.write(self.credentials.to_json())
            
            # Inicializa serviço do calendário
            self.service = build('calendar', 'v3', credentials=self.credentials)
            return True
            
        except Exception as e:
            print(f"Erro na autenticação: {e}")
            return False
    
    def get_service(self):
        """
        Retorna o serviço do Google Calendar, autenticando se necessário.
        
        Returns:
            Objeto service do Google Calendar API
        """
        if not self.service:
            self.authenticate()
        return self.service
    
    def create_meeting_event(
        self,
        summary: str,
        description: str,
        start_datetime: datetime,
        end_datetime: datetime,
        attendee_emails: List[str],
        timezone: str = "America/Sao_Paulo",
        location: Optional[str] = None,
        send_notifications: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Cria um evento de reunião no Google Calendar.
        
        Args:
            summary: Título da reunião
            description: Descrição detalhada
            start_datetime: Data/hora de início
            end_datetime: Data/hora de término
            attendee_emails: Lista de emails dos participantes
            timezone: Fuso horário (padrão: America/Sao_Paulo)
            location: Local da reunião (opcional)
            send_notifications: Se deve enviar emails de notificação
            
        Returns:
            Dicionário com dados do evento criado ou None em caso de erro
        """
        try:
            service = self.get_service()
            
            # Monta estrutura do evento
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': timezone,
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': timezone,
                },
                'attendees': [{'email': email} for email in attendee_emails],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 dia antes
                        {'method': 'popup', 'minutes': 30},        # 30 min antes
                    ],
                },
                'conferenceData': {
                    'createRequest': {
                        'requestId': f"meet-{datetime.now().timestamp()}",
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                    }
                }
            }
            
            if location:
                event['location'] = location
            
            # Cria evento
            created_event = service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all' if send_notifications else 'none',
                conferenceDataVersion=1  # Habilita Google Meet
            ).execute()
            
            return {
                'id': created_event['id'],
                'htmlLink': created_event.get('htmlLink'),
                'hangoutLink': created_event.get('hangoutLink'),
                'summary': created_event.get('summary'),
                'start': created_event['start'].get('dateTime'),
                'end': created_event['end'].get('dateTime'),
                'status': created_event.get('status')
            }
            
        except HttpError as error:
            print(f"Erro ao criar evento: {error}")
            return None
    
    def check_time_slot_available(
        self,
        date: datetime.date,
        start_time: str,
        end_time: str,
        timezone: str = "America/Sao_Paulo"
    ) -> bool:
        """
        Verifica se um horário está disponível (sem conflitos).
        
        Args:
            date: Data da reunião
            start_time: Hora de início (formato "HH:MM")
            end_time: Hora de término (formato "HH:MM")
            timezone: Fuso horário
            
        Returns:
            True se horário está livre, False se há conflito
        """
        try:
            service = self.get_service()
            
            # Converte para datetime
            start_hour, start_min = map(int, start_time.split(':'))
            end_hour, end_min = map(int, end_time.split(':'))
            
            start_dt = datetime.combine(date, datetime.min.time().replace(
                hour=start_hour, minute=start_min
            ))
            end_dt = datetime.combine(date, datetime.min.time().replace(
                hour=end_hour, minute=end_min
            ))
            
            # Busca eventos no intervalo
            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_dt.isoformat() + 'Z',
                timeMax=end_dt.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Se não há eventos, horário está livre
            return len(events) == 0
            
        except HttpError as error:
            print(f"Erro ao verificar disponibilidade: {error}")
            return False
    
    def get_available_slots(
        self,
        date,
        start_hour: int = 9,
        end_hour: int = 18,
        slot_duration_minutes: int = 60,
        timezone: str = "America/Sao_Paulo"
    ) -> List[Dict[str, str]]:
        """
        Retorna todos os horários livres em um dia.
        
        Args:
            date: Data para buscar horários
            start_hour: Hora de início do expediente (padrão: 9h)
            end_hour: Hora de fim do expediente (padrão: 18h)
            slot_duration_minutes: Duração de cada slot em minutos
            timezone: Fuso horário
            
        Returns:
            Lista de dicts com start e end (formato "HH:MM")
        """
        try:
            service = self.get_service()
            
            # Define início e fim do dia
            day_start = datetime.combine(date, datetime.min.time().replace(hour=start_hour))
            day_end = datetime.combine(date, datetime.min.time().replace(hour=end_hour))
            
            # Busca eventos ocupados nesse dia
            events_result = service.events().list(
                calendarId='primary',
                timeMin=day_start.isoformat() + 'Z',
                timeMax=day_end.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Converte eventos para intervalos ocupados
            busy_intervals = []
            for event in events:
                start_str = event['start'].get('dateTime')
                end_str = event['end'].get('dateTime')
                
                if start_str and end_str:
                    # Remove timezone info para comparação
                    start = datetime.fromisoformat(start_str.replace('Z', '+00:00')).replace(tzinfo=None)
                    end = datetime.fromisoformat(end_str.replace('Z', '+00:00')).replace(tzinfo=None)
                    busy_intervals.append((start, end))
            
            # Gera todos os slots possíveis
            available_slots = []
            current = day_start
            slot_duration = timedelta(minutes=slot_duration_minutes)
            
            while current + slot_duration <= day_end:
                slot_end = current + slot_duration
                
                # Verifica se o slot conflita com algum evento
                is_free = True
                for busy_start, busy_end in busy_intervals:
                    # Há conflito se os intervalos se sobrepõem
                    if not (slot_end <= busy_start or current >= busy_end):
                        is_free = False
                        break
                
                if is_free:
                    available_slots.append({
                        "start": current.strftime("%H:%M"),
                        "end": slot_end.strftime("%H:%M")
                    })
                
                # Avança para o próximo slot
                current += slot_duration
            
            return available_slots
            
        except HttpError as error:
            print(f"Erro ao buscar slots disponíveis: {error}")
            return []
    
    def list_upcoming_events(
        self,
        max_results: int = 10,
        days_ahead: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Lista próximos eventos do calendário.
        
        Args:
            max_results: Número máximo de eventos a retornar
            days_ahead: Quantos dias à frente buscar
            
        Returns:
            Lista de dicionários com dados dos eventos
        """
        try:
            service = self.get_service()
            
            # Define intervalo de busca
            now = datetime.utcnow().isoformat() + 'Z'
            future = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + 'Z'
            
            # Busca eventos
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now,
                timeMax=future,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Formata resposta
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                formatted_events.append({
                    'id': event['id'],
                    'summary': event.get('summary', 'Sem título'),
                    'start': start,
                    'end': event['end'].get('dateTime', event['end'].get('date')),
                    'location': event.get('location'),
                    'attendees': [a.get('email') for a in event.get('attendees', [])],
                    'htmlLink': event.get('htmlLink'),
                    'hangoutLink': event.get('hangoutLink')
                })
            
            return formatted_events
            
        except HttpError as error:
            print(f"Erro ao listar eventos: {error}")
            return []
    
    def update_event(
        self,
        event_id: str,
        updates: Dict[str, Any],
        send_notifications: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Atualiza um evento existente.
        
        Args:
            event_id: ID do evento no Google Calendar
            updates: Dicionário com campos a atualizar (summary, start, end, etc)
            send_notifications: Se deve notificar participantes
            
        Returns:
            Dicionário com dados do evento atualizado ou None em erro
        """
        try:
            service = self.get_service()
            
            # Busca evento atual
            event = service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Aplica atualizações
            event.update(updates)
            
            # Salva mudanças
            updated_event = service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event,
                sendUpdates='all' if send_notifications else 'none'
            ).execute()
            
            return {
                'id': updated_event['id'],
                'summary': updated_event.get('summary'),
                'start': updated_event['start'].get('dateTime'),
                'end': updated_event['end'].get('dateTime'),
                'status': updated_event.get('status')
            }
            
        except HttpError as error:
            print(f"Erro ao atualizar evento: {error}")
            return None
    
    def cancel_event(
        self,
        event_id: str,
        send_notifications: bool = True
    ) -> bool:
        """
        Cancela (deleta) um evento do calendário.
        
        Args:
            event_id: ID do evento
            send_notifications: Se deve notificar participantes
            
        Returns:
            True se cancelamento foi bem sucedido
        """
        try:
            service = self.get_service()
            
            service.events().delete(
                calendarId='primary',
                eventId=event_id,
                sendUpdates='all' if send_notifications else 'none'
            ).execute()
            
            return True
            
        except HttpError as error:
            print(f"Erro ao cancelar evento: {error}")
            return False
    
    def get_available_slots(
        self,
        date: datetime.date,
        business_hours_start: str = "09:00",
        business_hours_end: str = "18:00",
        slot_duration_minutes: int = 60,
        break_between_meetings: int = 15
    ) -> List[Dict[str, str]]:
        """
        Retorna horários disponíveis em um dia específico.
        
        Args:
            date: Data para verificar
            business_hours_start: Início do horário comercial
            business_hours_end: Fim do horário comercial
            slot_duration_minutes: Duração de cada slot
            break_between_meetings: Intervalo entre reuniões (minutos)
            
        Returns:
            Lista de dicts com 'start' e 'end' dos horários livres
        """
        try:
            service = self.get_service()
            
            # Define intervalo do dia
            start_of_day = datetime.combine(
                date,
                datetime.strptime(business_hours_start, "%H:%M").time()
            )
            end_of_day = datetime.combine(
                date,
                datetime.strptime(business_hours_end, "%H:%M").time()
            )
            
            # Busca eventos do dia
            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_of_day.isoformat() + 'Z',
                timeMax=end_of_day.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Monta lista de horários ocupados
            busy_slots = []
            for event in events:
                start = datetime.fromisoformat(
                    event['start'].get('dateTime', event['start'].get('date')).replace('Z', '')
                )
                end = datetime.fromisoformat(
                    event['end'].get('dateTime', event['end'].get('date')).replace('Z', '')
                )
                busy_slots.append((start, end))
            
            # Calcula horários livres
            available_slots = []
            current_time = start_of_day
            
            while current_time + timedelta(minutes=slot_duration_minutes) <= end_of_day:
                slot_end = current_time + timedelta(minutes=slot_duration_minutes)
                
                # Verifica se slot não conflita com eventos existentes
                is_free = True
                for busy_start, busy_end in busy_slots:
                    if not (slot_end <= busy_start or current_time >= busy_end):
                        is_free = False
                        break
                
                if is_free:
                    available_slots.append({
                        'start': current_time.strftime("%H:%M"),
                        'end': slot_end.strftime("%H:%M")
                    })
                
                current_time += timedelta(minutes=slot_duration_minutes + break_between_meetings)
            
            return available_slots
            
        except HttpError as error:
            print(f"Erro ao buscar slots disponíveis: {error}")
            return []


# Exemplo de uso
if __name__ == "__main__":
    # Inicializa serviço
    calendar_service = GoogleCalendarService()
    
    # Autentica
    if calendar_service.authenticate():
        print("✓ Autenticação realizada com sucesso!")
        
        # Lista próximos eventos
        print("\n📅 Próximos eventos:")
        events = calendar_service.list_upcoming_events(max_results=5)
        for event in events:
            print(f"  - {event['summary']} em {event['start']}")
        
        # Verifica disponibilidade
        from datetime import date
        tomorrow = date.today() + timedelta(days=1)
        is_available = calendar_service.check_time_slot_available(
            tomorrow, "14:00", "15:00"
        )
        print(f"\n⏰ Horário 14:00-15:00 amanhã: {'Disponível' if is_available else 'Ocupado'}")
        
        # Busca slots disponíveis
        print(f"\n🕐 Horários disponíveis amanhã:")
        slots = calendar_service.get_available_slots(tomorrow)
        for slot in slots[:5]:  # Mostra apenas 5 primeiros
            print(f"  - {slot['start']} às {slot['end']}")
        
        # Exemplo de criação de evento (comentado para não criar de verdade)
        # event_data = calendar_service.create_meeting_event(
        #     summary="Reunião de Demonstração",
        #     description="Apresentação do produto para lead qualificado",
        #     start_datetime=datetime.now() + timedelta(days=2, hours=3),
        #     end_datetime=datetime.now() + timedelta(days=2, hours=4),
        #     attendee_emails=["lead@empresa.com", "vendedor@empresa.com"],
        #     location="Google Meet"
        # )
        # if event_data:
        #     print(f"\n✓ Evento criado: {event_data['htmlLink']}")
        #     print(f"  Link Google Meet: {event_data['hangoutLink']}")
    else:
        print("✗ Falha na autenticação")
