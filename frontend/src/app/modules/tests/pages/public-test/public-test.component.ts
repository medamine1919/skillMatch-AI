import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { TestService } from '../../../../services/test.service';

interface PublicQuestion { question: string; options: string[]; }

/**
 * ============================================================================
 *  PublicTestComponent — page de passage du test (CANDIDAT, sans login).
 * ----------------------------------------------------------------------------
 *  Composant STANDALONE accessible publiquement via /test?token=...
 *  Étapes : charge le test (jeton) -> affiche le QCM -> soumet -> affiche le score.
 *  Aucune donnée sensible n'est exposée (les bonnes réponses restent au serveur).
 * ============================================================================
 */
@Component({
  selector: 'app-public-test',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './public-test.component.html',
  styleUrls: ['./public-test.component.css']
})
export class PublicTestComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private testService = inject(TestService);

  token = '';
  loading = true;
  error: string | null = null;

  candidateName = '';
  jobTitle = '';
  status = '';                      // PENDING / COMPLETED / EXPIRED
  questions: PublicQuestion[] = [];
  answers: (number | null)[] = [];  // index choisi par question

  submitting = false;
  result: { scorePercent: number; correctCount: number; totalQuestions: number; passed: boolean } | null = null;

  ngOnInit(): void {
    this.token = this.route.snapshot.queryParamMap.get('token') || '';
    if (!this.token) { this.error = 'Lien de test invalide.'; this.loading = false; return; }
    this.loadTest();
  }

  private loadTest(): void {
    this.testService.getPublicTest(this.token).subscribe({
      next: (data) => {
        this.candidateName = data.candidateName || '';
        this.jobTitle = data.jobTitle || '';
        this.status = data.status || '';
        this.questions = data.questions || [];
        this.answers = this.questions.map(() => null);
        // Test déjà passé : on affiche directement le résultat.
        if (this.status === 'COMPLETED') {
          this.result = { scorePercent: data.scorePercent, correctCount: 0,
                          totalQuestions: data.totalQuestions, passed: data.passed };
        }
        this.loading = false;
      },
      error: (e) => { this.error = e?.error?.error || 'Test introuvable ou expiré.'; this.loading = false; }
    });
  }

  /** Toutes les questions ont-elles une réponse ? */
  get allAnswered(): boolean {
    return this.questions.length > 0 && this.answers.every(a => a !== null);
  }

  select(qIndex: number, optIndex: number): void {
    this.answers[qIndex] = optIndex;
  }

  submit(): void {
    if (!this.allAnswered || this.submitting) return;
    this.submitting = true;
    this.testService.submitTest(this.token, this.answers as number[]).subscribe({
      next: (res) => { this.result = res; this.status = 'COMPLETED'; this.submitting = false; },
      error: (e) => { this.error = e?.error?.error || "Erreur lors de l'envoi des réponses."; this.submitting = false; }
    });
  }
}
