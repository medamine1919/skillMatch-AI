import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

/**
 * ============================================================================
 *  IconComponent — icônes SVG professionnelles (style "ligne", type Lucide).
 * ----------------------------------------------------------------------------
 *  Remplace les emojis par de vrais SVG vectoriels, nets et cohérents.
 *  - Composant STANDALONE : s'importe dans n'importe quel module.
 *  - Les SVG utilisent `currentColor` -> l'icône prend la couleur du texte
 *    environnant (donc thématisable via CSS, comme une police).
 *
 *  Utilisation dans un template :
 *     <app-icon name="home"></app-icon>
 *     <app-icon name="search" size="18"></app-icon>
 *     <app-icon name="trash" [size]="20"></app-icon>
 * ============================================================================
 */
@Component({
  selector: 'app-icon',
  standalone: true,
  imports: [CommonModule],
  template: `<span class="app-icon" [style.width.px]="size" [style.height.px]="size"
                  [innerHTML]="svg"></span>`,
  styles: [`
    .app-icon { display: inline-flex; align-items: center; justify-content: center;
                line-height: 0; vertical-align: middle; }
    .app-icon ::ng-deep svg { width: 100%; height: 100%; display: block; }
  `]
})
export class IconComponent {
  /** Nom de l'icône (clé du dictionnaire ICONS). */
  @Input() set name(value: string) { this._name = value; this.render(); }
  /** Taille en pixels (largeur = hauteur). */
  @Input() size: number | string = 20;

  private _name = '';
  svg: SafeHtml = '';

  constructor(private sanitizer: DomSanitizer) {}

  private render(): void {
    const body = ICONS[this._name] || ICONS['dot'];
    // viewBox 24x24, trait = couleur du texte courant, style Lucide.
    const markup =
      `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ` +
      `stroke-linecap="round" stroke-linejoin="round">${body}</svg>`;
    this.svg = this.sanitizer.bypassSecurityTrustHtml(markup);
  }
}

/**
 * Dictionnaire des icônes (contenu intérieur du <svg>, en 24x24).
 * Tracés inspirés de Lucide (open-source, licence ISC).
 */
export const ICONS: Record<string, string> = {
  dot: `<circle cx="12" cy="12" r="2"/>`,

  // Navigation
  home: `<path d="M3 9.5 12 3l9 6.5"/><path d="M5 10v10h14V10"/><path d="M9 20v-6h6v6"/>`,
  upload: `<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 9l5-5 5 5"/><path d="M12 4v12"/>`,
  dashboard: `<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>`,
  users: `<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>`,
  settings: `<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>`,
  analytics: `<path d="M3 3v18h18"/><path d="M7 15l3-4 3 3 4-6"/>`,
  power: `<path d="M12 2v10"/><path d="M18.4 6.6a9 9 0 1 1-12.8 0"/>`,

  // Brand
  target: `<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>`,

  // Actions
  search: `<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>`,
  trash: `<path d="M3 6h18"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/>`,
  restore: `<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/>`,
  download: `<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5"/><path d="M12 15V3"/>`,
  refresh: `<path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><path d="M21 3v5h-5"/>`,
  eye: `<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/>`,
  filter: `<path d="M3 4h18l-7 8v6l-4 2v-8z"/>`,
  edit: `<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>`,
  plus: `<path d="M12 5v14"/><path d="M5 12h14"/>`,

  // Statuts
  check: `<path d="M20 6 9 17l-5-5"/>`,
  'check-circle': `<circle cx="12" cy="12" r="9"/><path d="m9 12 2 2 4-4"/>`,
  close: `<path d="M18 6 6 18"/><path d="m6 6 12 12"/>`,
  warning: `<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12" y2="17.01"/>`,
  info: `<circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16"/><line x1="12" y1="8" x2="12" y2="8.01"/>`,
  lightbulb: `<path d="M9 18h6"/><path d="M10 22h4"/><path d="M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2.1h6c0-.8.4-1.6 1-2.1A7 7 0 0 0 12 2z"/>`,
  clock: `<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>`,
  ban: `<circle cx="12" cy="12" r="9"/><path d="m4.9 4.9 14.2 14.2"/>`,

  // Contenu / profil
  mail: `<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m2 6 10 7 10-7"/>`,
  phone: `<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6 19.8 19.8 0 0 1-3.1-8.7A2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z"/>`,
  user: `<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>`,
  lock: `<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>`,
  briefcase: `<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>`,
  graduation: `<path d="M22 10 12 5 2 10l10 5 10-5z"/><path d="M6 12v5c0 1 2.7 2.5 6 2.5s6-1.5 6-2.5v-5"/>`,
  document: `<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M8 13h8"/><path d="M8 17h8"/>`,
  location: `<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/>`,
  globe: `<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a15 15 0 0 1 0 18 15 15 0 0 1 0-18z"/>`,
  award: `<circle cx="12" cy="8" r="6"/><path d="M8.2 13.4 7 22l5-3 5 3-1.2-8.6"/>`,
  rocket: `<path d="M4.5 16.5c-1.5 1.3-2 5-2 5s3.7-.5 5-2c.7-.8.7-2 0-2.8a2 2 0 0 0-3 0z"/><path d="M12 15l-3-3a11 11 0 0 1 7-8 11 11 0 0 1 4 0 11 11 0 0 1 0 4 11 11 0 0 1-8 7z"/><path d="M9 12H4l4-4"/><path d="M12 15v5l4-4"/>`,
  cpu: `<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>`,
  'trending-up': `<path d="m3 17 6-6 4 4 8-8"/><path d="M17 7h4v4"/>`,
  star: `<path d="m12 3 2.9 5.9 6.5.9-4.7 4.6 1.1 6.5L12 18l-5.8 3 1.1-6.5L2.6 9.8l6.5-.9z"/>`,

  // Compléments
  zap: `<path d="M13 2 4 14h7l-1 8 9-12h-7l1-8z"/>`,
  clipboard: `<rect x="8" y="3" width="8" height="4" rx="1"/><path d="M16 5h2a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h2"/>`,
  inbox: `<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.5 5.1 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.5-6.9A2 2 0 0 0 16.8 4H7.2a2 2 0 0 0-1.7 1.1z"/>`,
  'arrow-right': `<path d="M5 12h14"/><path d="m13 6 6 6-6 6"/>`,
  'arrow-left': `<path d="M19 12H5"/><path d="m11 18-6-6 6-6"/>`,
  'arrow-left-right': `<path d="M8 3 4 7l4 4"/><path d="M4 7h16"/><path d="m16 21 4-4-4-4"/><path d="M20 17H4"/>`,
  smile: `<circle cx="12" cy="12" r="9"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9" y2="9.01"/><line x1="15" y1="9" x2="15" y2="9.01"/>`,
  folder: `<path d="M4 20a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2z"/>`,
  building: `<rect x="4" y="3" width="16" height="18" rx="1"/><path d="M9 7h2M13 7h2M9 11h2M13 11h2M9 15h2M13 15h2"/>`,
  sparkles: `<path d="M12 3v6M12 15v6M3 12h6M15 12h6"/><path d="m6 6 3 3M15 15l3 3M18 6l-3 3M9 15l-3 3"/>`,
  scale: `<path d="M12 3v18"/><path d="M7 21h10"/><path d="M5 7h14"/><path d="m5 7-3 6h6z"/><path d="m19 7-3 6h6z"/>`,
};
