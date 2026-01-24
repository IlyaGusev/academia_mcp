import sys
from typing import Optional

from rich.console import Console
from rich.table import Table

from academia_mcp.auth.token_manager import issue_token as _issue_token
from academia_mcp.auth.token_manager import list_tokens as _list_tokens
from academia_mcp.auth.token_manager import revoke_token as _revoke_token


class AuthCLI:
    def issue_token(
        self,
        client_id: str,
        scopes: str = "*",
        expires_days: Optional[int] = None,
        description: str = "",
    ) -> None:
        scope_list = [s.strip() for s in scopes.split(",")]

        metadata = _issue_token(client_id, scope_list, expires_days, description)

        console = Console()
        console.print("\n[green]Token issued successfully![/green]\n")
        console.print(f"Token: [bold yellow]{metadata.token_id}[/bold yellow]\n")
        console.print("[red]IMPORTANT: Copy this token now. It will not be shown again.[/red]\n")
        console.print(f"Client ID: {metadata.client_id}")
        console.print(f"Scopes: {', '.join(metadata.scopes)}")
        if metadata.expires_at:
            console.print(f"Expires: {metadata.expires_at.isoformat()}")
        else:
            console.print("Expires: Never")

    def list_tokens(self) -> None:
        tokens = _list_tokens()

        console = Console()

        if not tokens:
            console.print("[yellow]No active tokens found[/yellow]")
            return

        table = Table(title="Active Tokens")
        table.add_column("Token ID (prefix)", style="cyan")
        table.add_column("Client ID", style="green")
        table.add_column("Issued At")
        table.add_column("Expires At")
        table.add_column("Last Used")

        for token in tokens:
            token_preview = token.token_id[:16] + "..."
            expires = token.expires_at.isoformat() if token.expires_at else "Never"
            last_used = token.last_used.isoformat() if token.last_used else "Never"

            table.add_row(
                token_preview,
                token.client_id,
                token.issued_at.isoformat(),
                expires,
                last_used,
            )

        console.print(table)

    def revoke_token(self, token_id: str) -> None:
        success = _revoke_token(token_id)
        console = Console()
        if success:
            console.print(f"[green]Token {token_id} revoked successfully[/green]")
        else:
            console.print(f"[red]Token {token_id} not found[/red]")
            sys.exit(1)
