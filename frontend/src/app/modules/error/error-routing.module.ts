import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { UnauthorizedComponent } from './pages/unauthorized/unauthorized.component';
import { InvalidDocumentComponent } from './pages/invalid-document/invalid-document.component';

const routes: Routes = [
  { path: '', component: UnauthorizedComponent },
  { path: 'invalid-document', component: InvalidDocumentComponent }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ErrorRoutingModule { }
