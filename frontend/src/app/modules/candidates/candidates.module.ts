import { NgModule } from '@angular/core';
import { IconComponent } from '../../shared/icon/icon.component';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { CandidatesRoutingModule } from './candidates-routing.module';
import { CandidatesComponent } from './pages/candidates/candidates.component';
import { CandidateDetailComponent } from './pages/candidate-detail/candidate-detail.component';

@NgModule({
  declarations: [
    CandidatesComponent,
    CandidateDetailComponent
  ],
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    CandidatesRoutingModule, IconComponent
  ]
})
export class CandidatesModule { }
