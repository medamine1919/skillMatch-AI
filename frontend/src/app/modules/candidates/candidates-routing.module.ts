import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { CandidatesComponent } from './pages/candidates/candidates.component';
import { CandidateDetailComponent } from './pages/candidate-detail/candidate-detail.component';

const routes: Routes = [
  { path: '', component: CandidatesComponent },
  { path: ':id', component: CandidateDetailComponent }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class CandidatesRoutingModule { }
