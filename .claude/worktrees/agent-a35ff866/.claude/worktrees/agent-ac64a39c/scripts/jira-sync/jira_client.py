"""
Cliente para a API REST do Jira.

Este módulo fornece funções para interagir com a API do Jira,
incluindo criar, atualizar e buscar issues.
"""

import os
import requests
from typing import Dict, Any, List, Optional
from requests.auth import HTTPBasicAuth


class JiraClient:
    """Cliente para interação com a API do Jira."""
    
    def __init__(
        self,
        email: Optional[str] = None,
        api_token: Optional[str] = None,
        base_url: Optional[str] = None,
        project_key: Optional[str] = None
    ):
        """
        Inicializa o cliente Jira.
        
        Args:
            email: Email da conta Jira (ou JIRA_EMAIL env var)
            api_token: Token de API do Jira (ou JIRA_API_TOKEN env var)
            base_url: URL base do Jira (ou JIRA_BASE_URL env var)
            project_key: Chave do projeto (ou JIRA_PROJECT_KEY env var)
        """
        self.email = email or os.environ.get('JIRA_EMAIL')
        self.api_token = api_token or os.environ.get('JIRA_API_TOKEN')
        self.base_url = (base_url or os.environ.get('JIRA_BASE_URL', 'https://wedotalent.atlassian.net')).rstrip('/')
        self.project_key = project_key or os.environ.get('JIRA_PROJECT_KEY', 'WT')
        
        self._validate_credentials()
        
        self.auth = HTTPBasicAuth(self.email, self.api_token)
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def _validate_credentials(self):
        """Valida se as credenciais estão configuradas."""
        if not self.email:
            raise ValueError(
                "JIRA_EMAIL não configurado. "
                "Defina a variável de ambiente ou passe no construtor."
            )
        if not self.api_token:
            raise ValueError(
                "JIRA_API_TOKEN não configurado. "
                "Defina a variável de ambiente ou passe no construtor."
            )
    
    def _api_url(self, endpoint: str) -> str:
        """Constrói a URL completa da API."""
        return f"{self.base_url}/rest/api/3/{endpoint.lstrip('/')}"
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Faz uma requisição à API do Jira.
        
        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint da API
            data: Dados para enviar (JSON)
            params: Parâmetros de query string
            
        Returns:
            Resposta da API como dicionário
            
        Raises:
            JiraAPIError: Se a requisição falhar
        """
        url = self._api_url(endpoint)
        
        try:
            response = requests.request(
                method=method,
                url=url,
                auth=self.auth,
                headers=self.headers,
                json=data,
                params=params,
                timeout=30
            )
            
            if response.status_code == 204:
                return {}
            
            if response.status_code >= 400:
                error_data = response.json() if response.text else {}
                raise JiraAPIError(
                    status_code=response.status_code,
                    message=error_data.get('errorMessages', [str(error_data)]),
                    errors=error_data.get('errors', {})
                )
            
            if response.text:
                return response.json()
            return {}
            
        except requests.RequestException as e:
            raise JiraAPIError(
                status_code=0,
                message=[f"Erro de conexão: {str(e)}"],
                errors={}
            )
    
    def test_connection(self) -> bool:
        """
        Testa a conexão com o Jira.
        
        Returns:
            True se a conexão for bem sucedida
        """
        try:
            self._request('GET', 'myself')
            return True
        except JiraAPIError:
            return False
    
    def get_project_info(self) -> Dict[str, Any]:
        """
        Obtém informações do projeto configurado.
        
        Returns:
            Dados do projeto
        """
        return self._request('GET', f'project/{self.project_key}')
    
    def get_issue_types(self) -> List[Dict[str, Any]]:
        """
        Lista os tipos de issue disponíveis no projeto.
        
        Returns:
            Lista de tipos de issue
        """
        project = self.get_project_info()
        return project.get('issueTypes', [])
    
    def get_priorities(self) -> List[Dict[str, Any]]:
        """
        Lista as prioridades disponíveis.
        
        Returns:
            Lista de prioridades
        """
        return self._request('GET', 'priority')
    
    def get_transitions(self, issue_key: str) -> List[Dict[str, Any]]:
        """
        Obtém as transições disponíveis para uma issue.
        
        Args:
            issue_key: Chave da issue (ex: WT-123)
            
        Returns:
            Lista de transições disponíveis
        """
        result = self._request('GET', f'issue/{issue_key}/transitions')
        return result.get('transitions', [])
    
    def search_issues(self, jql: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Busca issues usando JQL.
        
        Args:
            jql: Query JQL
            max_results: Número máximo de resultados
            
        Returns:
            Lista de issues encontradas
        """
        result = self._request('GET', 'search/jql', params={
            'jql': jql,
            'maxResults': max_results,
            'fields': 'summary,status,priority,labels,issuetype'
        })
        return result.get('issues', [])
    
    def find_issue_by_card_id(self, card_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca uma issue pelo ID do card (via label).
        
        Args:
            card_id: ID do card (ex: EMP-001)
            
        Returns:
            Issue encontrada ou None
        """
        jql = f'project = {self.project_key} AND labels = "card-id:{card_id}"'
        issues = self.search_issues(jql, max_results=1)
        
        if issues:
            return issues[0]
        
        jql = f'project = {self.project_key} AND summary ~ "[{card_id}]"'
        issues = self.search_issues(jql, max_results=1)
        
        return issues[0] if issues else None
    
    def create_issue(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria uma nova issue no Jira.
        
        Args:
            payload: Dados da issue no formato da API
            
        Returns:
            Issue criada
        """
        return self._request('POST', 'issue', data=payload)
    
    def update_issue(self, issue_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza uma issue existente.
        
        Args:
            issue_key: Chave da issue (ex: WT-123)
            payload: Dados para atualizar
            
        Returns:
            Issue atualizada
        """
        return self._request('PUT', f'issue/{issue_key}', data=payload)
    
    def transition_issue(self, issue_key: str, transition_id: str) -> Dict[str, Any]:
        """
        Move uma issue para outro status.
        
        Args:
            issue_key: Chave da issue
            transition_id: ID da transição
            
        Returns:
            Resultado da transição
        """
        return self._request('POST', f'issue/{issue_key}/transitions', data={
            'transition': {'id': transition_id}
        })
    
    def move_to_todo(self, issue_key: str) -> bool:
        """
        Move uma issue para o status "To Do".
        
        Args:
            issue_key: Chave da issue
            
        Returns:
            True se moveu com sucesso
        """
        transitions = self.get_transitions(issue_key)
        
        for transition in transitions:
            name = transition.get('name', '').lower()
            if 'to do' in name or 'todo' in name or 'a fazer' in name:
                self.transition_issue(issue_key, transition['id'])
                return True
        
        return False
    
    def get_issue_url(self, issue_key: str) -> str:
        """
        Retorna a URL da issue no Jira.
        
        Args:
            issue_key: Chave da issue
            
        Returns:
            URL completa da issue
        """
        return f"{self.base_url}/browse/{issue_key}"


class JiraAPIError(Exception):
    """Exceção para erros da API do Jira."""
    
    def __init__(self, status_code: int, message: List[str], errors: Dict[str, Any]):
        self.status_code = status_code
        self.messages = message
        self.errors = errors
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Formata a mensagem de erro."""
        msg = f"Jira API Error (HTTP {self.status_code})"
        
        if self.messages:
            msg += f": {'; '.join(self.messages)}"
        
        if self.errors:
            error_details = ', '.join(f"{k}: {v}" for k, v in self.errors.items())
            msg += f" | Detalhes: {error_details}"
        
        return msg


def check_credentials() -> Dict[str, bool]:
    """
    Verifica se as credenciais estão configuradas.
    
    Returns:
        Dicionário com status de cada credencial
    """
    return {
        'JIRA_EMAIL': bool(os.environ.get('JIRA_EMAIL')),
        'JIRA_API_TOKEN': bool(os.environ.get('JIRA_API_TOKEN')),
        'JIRA_BASE_URL': bool(os.environ.get('JIRA_BASE_URL')),
        'JIRA_PROJECT_KEY': bool(os.environ.get('JIRA_PROJECT_KEY')),
    }


if __name__ == '__main__':
    print("Verificando credenciais do Jira...")
    print("=" * 50)
    
    creds = check_credentials()
    
    for key, configured in creds.items():
        status = "✓ Configurado" if configured else "✗ Não configurado"
        print(f"  {key}: {status}")
    
    print()
    
    if creds['JIRA_EMAIL'] and creds['JIRA_API_TOKEN']:
        print("Testando conexão...")
        try:
            client = JiraClient()
            if client.test_connection():
                print("✓ Conexão bem sucedida!")
                
                print("\nInformações do projeto:")
                try:
                    project = client.get_project_info()
                    print(f"  Nome: {project.get('name')}")
                    print(f"  Chave: {project.get('key')}")
                except JiraAPIError as e:
                    print(f"  Erro ao obter projeto: {e}")
            else:
                print("✗ Falha na conexão")
        except ValueError as e:
            print(f"✗ Erro de configuração: {e}")
        except JiraAPIError as e:
            print(f"✗ Erro da API: {e}")
    else:
        print("Configure as credenciais para testar a conexão.")
