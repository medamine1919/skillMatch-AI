import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

/**
 * ============================================================================
 *  TestService — appels API du test technique (QCM).
 * ----------------------------------------------------------------------------
 *   - sendTest     : le recruteur envoie un test à un candidat (sécurisé) ;
 *   - listTests    : tableau de bord des tests (sécurisé) ;
 *   - getPublicTest / submitTest : passage du test par le candidat (PUBLIC,
 *     sans login, via le jeton du lien d'invitation).
 * ============================================================================
 */
@Injectable({ providedIn: 'root' })
export class TestService {
  private api = `${environment.apiUrl}/api`;
  private http = inject(HttpClient);

  /** Recruteur : envoyer un test au candidat correspondant à l'analyse `resultId`. */
  sendTest(resultId: string | number): Observable<any> {
    return this.http.post<any>(`${this.api}/cv-analysis/results/${resultId}/send-test`, {});
  }

  /** Recruteur : liste de tous les tests (dashboard). */
  listTests(): Observable<any[]> {
    return this.http.get<any[]>(`${this.api}/tests`);
  }

  /** Candidat (public) : récupérer le test via son jeton. */
  getPublicTest(token: string): Observable<any> {
    return this.http.get<any>(`${this.api}/public/test/${token}`);
  }

  /** Candidat (public) : soumettre les réponses (indices choisis par question). */
  submitTest(token: string, answers: number[]): Observable<any> {
    return this.http.post<any>(`${this.api}/public/test/${token}/submit`, { answers });
  }
}
