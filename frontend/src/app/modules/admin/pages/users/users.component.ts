import { Component, OnInit, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { ActivatedRoute } from '@angular/router';
import { environment } from '../../../../../environments/environment';

interface UserItem {
  id: number;
  name: string;
  email: string;
  role: string;
  status: 'PENDING' | 'APPROVED' | 'DECLINED';
  createdAt: string;
  loading?: boolean;
}

@Component({
  selector: 'app-users',
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.css']
})
/**
 * ============================================================================
 *  UsersComponent — page "Gestion des accès" (réservée à l'admin).
 * ----------------------------------------------------------------------------
 *  Liste les utilisateurs et permet de les approuver / refuser / changer de rôle.
 *  Lit aussi les paramètres d'URL (?approved=, ?declined=) renvoyés quand l'admin
 *  a cliqué sur un lien depuis son e-mail, pour afficher un toast de confirmation.
 *  Chaque action met `user.loading=true` (désactive le bouton le temps de l'appel)
 *  et fait un "rollback visuel" en cas d'erreur (ex: changement de rôle).
 * ============================================================================
 */
export class UsersComponent implements OnInit {
  users: UserItem[] = [];
  loading = true;
  error: string | null = null;
  toast: { message: string; type: 'success' | 'error' } | null = null;
  filter: 'ALL' | 'PENDING' | 'APPROVED' | 'DECLINED' = 'ALL';   // filtre par statut

  private http = inject(HttpClient);
  private route = inject(ActivatedRoute);
  private apiUrl = `${environment.apiUrl}/api`;

  ngOnInit(): void {
    this.loadUsers();
    // Lire les paramètres de redirection depuis le lien email
    this.route.queryParams.subscribe(params => {
      if (params['approved']) this.showToast(`${params['approved']} a été approuvé avec succès.`, 'success');
      if (params['declined']) this.showToast(`${params['declined']} a été décliné.`, 'error');
      if (params['error']) this.showToast('Token invalide ou déjà utilisé.', 'error');
    });
  }

  loadUsers(): void {
    this.loading = true;
    this.error = null;
    const token = localStorage.getItem('access_token');
    const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });

    this.http.get<UserItem[]>(`${this.apiUrl}/admin/users`, { headers }).subscribe({
      next: (data) => { this.users = data; this.loading = false; },
      error: () => { this.error = 'Impossible de charger les utilisateurs.'; this.loading = false; }
    });
  }

  get filteredUsers(): UserItem[] {
    if (this.filter === 'ALL') return this.users;
    return this.users.filter(u => u.status === this.filter);
  }

  get pendingCount(): number { return this.users.filter(u => u.status === 'PENDING').length; }

  approve(user: UserItem): void {
    user.loading = true;
    const token = localStorage.getItem('access_token');
    const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });

    this.http.post<any>(`${this.apiUrl}/admin/users/${user.id}/approve`, {}, { headers }).subscribe({
      next: (res) => {
        user.status = 'APPROVED';
        user.role = 'RECRUITER';
        user.loading = false;
        this.showToast(`${user.name} a été approuvé et notifié par email.`, 'success');
      },
      error: () => { user.loading = false; this.showToast('Erreur lors de l\'approbation.', 'error'); }
    });
  }

  decline(user: UserItem): void {
    if (!confirm(`Décliner l'accès de ${user.name} ?`)) return;
    user.loading = true;
    const token = localStorage.getItem('access_token');
    const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });

    this.http.post<any>(`${this.apiUrl}/admin/users/${user.id}/decline`, {}, { headers }).subscribe({
      next: () => {
        user.status = 'DECLINED';
        user.loading = false;
        this.showToast(`Accès refusé pour ${user.name}.`, 'error');
      },
      error: () => { user.loading = false; this.showToast('Erreur lors du refus.', 'error'); }
    });
  }

  changeRole(user: UserItem, event: Event): void {
    const newRole = (event.target as HTMLSelectElement).value;
    if (newRole === user.role) return;
    const previous = user.role;
    user.loading = true;
    const token = localStorage.getItem('access_token');
    const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });

    this.http.post<any>(`${this.apiUrl}/admin/users/${user.id}/role`, { role: newRole }, { headers }).subscribe({
      next: () => {
        user.role = newRole;
        if (user.status !== 'APPROVED') user.status = 'APPROVED';
        user.loading = false;
        this.showToast(`Rôle de ${user.name} changé en ${newRole}.`, 'success');
      },
      error: () => {
        user.role = previous; // rollback visuel
        user.loading = false;
        this.showToast('Erreur lors du changement de rôle.', 'error');
      }
    });
  }

  showToast(message: string, type: 'success' | 'error'): void {
    this.toast = { message, type };
    setTimeout(() => this.toast = null, 4000);
  }

  getStatusBadge(status: string): string {
    switch (status) {
      case 'PENDING':  return 'badge-pending';
      case 'APPROVED': return 'badge-approved';
      case 'DECLINED': return 'badge-declined';
      default: return '';
    }
  }

  getStatusLabel(status: string): string {
    switch (status) {
      case 'PENDING':  return 'En attente';
      case 'APPROVED': return 'Approuvé';
      case 'DECLINED': return 'Décliné';
      default: return status;
    }
  }

  formatDate(dateStr: string): string {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  }
}
