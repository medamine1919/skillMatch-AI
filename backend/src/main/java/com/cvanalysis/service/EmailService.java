package com.cvanalysis.service;

import jakarta.mail.internet.MimeMessage;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;

/**
 * Service d'envoi d'emails via Gmail SMTP (JavaMailSender).
 * Complètement gratuit — utilise un compte Gmail + mot de passe d'application Google.
 */
@Service
public class EmailService {

    @Autowired
    private JavaMailSender mailSender;

    @Value("${brevo.admin-email}")
    private String adminEmail;

    @Value("${spring.mail.username}")
    private String senderEmail;

    @Value("${app.base-url}")
    private String appBaseUrl;

    @Value("${app.frontend-url}")
    private String frontendUrl;

    // =========================================================
    // Email à l'admin : nouvelle inscription en attente
    // =========================================================
    public void sendApprovalRequestToAdmin(String userName, String userEmail,
                                            String userId, String approvalToken) {
        String approveUrl = appBaseUrl + "/auth/approve/" + approvalToken;
        String declineUrl = appBaseUrl + "/auth/decline/" + approvalToken;
        String adminPanelUrl = frontendUrl + "/admin/users";

        String html = """
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
              <div style="background:#1F4E79;padding:24px;text-align:center">
                <h1 style="color:#fff;margin:0;font-size:22px">🎯 SkillMatch AI</h1>
                <p style="color:#90CAF9;margin:6px 0 0">Nouvelle demande d'inscription</p>
              </div>
              <div style="padding:28px">
                <p style="font-size:16px">Bonjour Administrateur,</p>
                <p>Un nouvel utilisateur s'est inscrit et attend votre approbation :</p>
                <table style="width:100%%;border-collapse:collapse;margin:16px 0">
                  <tr><td style="padding:8px;background:#f5f5f5;font-weight:bold;width:35%%">Nom</td>
                      <td style="padding:8px;border:1px solid #ddd">%s</td></tr>
                  <tr><td style="padding:8px;background:#f5f5f5;font-weight:bold">Email</td>
                      <td style="padding:8px;border:1px solid #ddd">%s</td></tr>
                  <tr><td style="padding:8px;background:#f5f5f5;font-weight:bold">Rôle attribué</td>
                      <td style="padding:8px;border:1px solid #ddd">RECRUITER</td></tr>
                </table>
                <p>Cliquez sur l'un des boutons ci-dessous :</p>
                <div style="text-align:center;margin:28px 0">
                  <a href="%s" style="background:#22c55e;color:#fff;padding:13px 36px;border-radius:6px;
                     text-decoration:none;font-size:16px;font-weight:bold;margin-right:12px">
                    ✅ Approuver
                  </a>
                  <a href="%s" style="background:#ef4444;color:#fff;padding:13px 36px;border-radius:6px;
                     text-decoration:none;font-size:16px;font-weight:bold">
                    ❌ Décliner
                  </a>
                </div>
                <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
                <p style="font-size:13px;color:#888">
                  Ou gérez les accès depuis le
                  <a href="%s" style="color:#1F4E79">panneau d'administration</a>.
                </p>
              </div>
            </div>
            """.formatted(userName, userEmail, approveUrl, declineUrl, adminPanelUrl);

        sendEmail(adminEmail,
                  "SkillMatch AI — Nouvelle inscription en attente : " + userName,
                  html);
    }

    // =========================================================
    // Email à l'utilisateur : compte approuvé
    // =========================================================
    public void sendApprovalConfirmation(String userName, String userEmail) {
        String loginUrl = frontendUrl + "/auth/login";
        String html = """
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
              <div style="background:#1F4E79;padding:24px;text-align:center">
                <h1 style="color:#fff;margin:0;font-size:22px">🎯 SkillMatch AI</h1>
              </div>
              <div style="padding:28px">
                <h2 style="color:#22c55e">🎉 Votre compte a été approuvé !</h2>
                <p>Bonjour <strong>%s</strong>,</p>
                <p>Votre compte SkillMatch AI a été approuvé. Vous pouvez maintenant vous connecter
                   avec le rôle <strong>Recruteur</strong> et accéder à toutes les fonctionnalités
                   de la plateforme.</p>
                <div style="text-align:center;margin:28px 0">
                  <a href="%s" style="background:#1F4E79;color:#fff;padding:13px 36px;border-radius:6px;
                     text-decoration:none;font-size:16px;font-weight:bold">
                    Se connecter
                  </a>
                </div>
                <p style="font-size:13px;color:#888">SkillMatch AI — DecliTech Innovation</p>
              </div>
            </div>
            """.formatted(userName, loginUrl);

        sendEmail(userEmail, "SkillMatch AI — Votre compte est activé ✅", html);
    }

    // =========================================================
    // Email à l'utilisateur : compte refusé
    // =========================================================
    public void sendDeclineNotification(String userName, String userEmail) {
        String html = """
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
              <div style="background:#1F4E79;padding:24px;text-align:center">
                <h1 style="color:#fff;margin:0;font-size:22px">🎯 SkillMatch AI</h1>
              </div>
              <div style="padding:28px">
                <h2 style="color:#ef4444">Demande d'accès non approuvée</h2>
                <p>Bonjour <strong>%s</strong>,</p>
                <p>Votre demande d'accès à la plateforme SkillMatch AI n'a pas été approuvée
                   par l'administrateur.</p>
                <p>Pour plus d'informations, contactez l'administrateur :
                   <a href="mailto:%s">%s</a></p>
                <p style="font-size:13px;color:#888">SkillMatch AI — DecliTech Innovation</p>
              </div>
            </div>
            """.formatted(userName, adminEmail, adminEmail);

        sendEmail(userEmail, "SkillMatch AI — Demande d'accès non approuvée", html);
    }

    // =========================================================
    // Email à l'utilisateur : lien de réinitialisation du mot de passe
    // =========================================================
    public void sendPasswordResetEmail(String userName, String userEmail, String resetToken) {
        // Le lien pointe vers la page Angular qui lira le token et demandera le nouveau mot de passe.
        String resetUrl = frontendUrl + "/auth/reset-password?token=" + resetToken;
        String html = """
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
              <div style="background:#1F4E79;padding:24px;text-align:center">
                <h1 style="color:#fff;margin:0;font-size:22px">SkillMatch AI</h1>
              </div>
              <div style="padding:28px">
                <h2 style="color:#1F4E79">Réinitialisation du mot de passe</h2>
                <p>Bonjour <strong>%s</strong>,</p>
                <p>Vous avez demandé à réinitialiser votre mot de passe. Cliquez sur le bouton
                   ci-dessous pour en choisir un nouveau. Ce lien est valable <strong>1 heure</strong>.</p>
                <div style="text-align:center;margin:28px 0">
                  <a href="%s" style="background:#1F4E79;color:#fff;padding:13px 36px;border-radius:6px;
                     text-decoration:none;font-size:16px;font-weight:bold">
                    Réinitialiser mon mot de passe
                  </a>
                </div>
                <p style="font-size:13px;color:#888">Si vous n'êtes pas à l'origine de cette demande,
                   ignorez simplement cet e-mail : votre mot de passe restera inchangé.</p>
              </div>
            </div>
            """.formatted(userName, resetUrl);

        sendEmail(userEmail, "SkillMatch AI — Réinitialisation de votre mot de passe", html);
    }

    // =========================================================
    // Email au candidat : invitation à passer un test technique
    // =========================================================
    public void sendTestInvitation(String candidateName, String candidateEmail,
                                   String token, String jobTitle) {
        // Lien vers la page publique de passage du test (sans login).
        String testUrl = frontendUrl + "/test?token=" + token;
        String html = """
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
              <div style="background:#1F4E79;padding:24px;text-align:center">
                <h1 style="color:#fff;margin:0;font-size:22px">SkillMatch AI</h1>
                <p style="color:#90CAF9;margin:6px 0 0">Invitation à un test technique</p>
              </div>
              <div style="padding:28px">
                <p>Bonjour <strong>%s</strong>,</p>
                <p>Suite à l'étude de votre candidature, le recruteur vous invite à passer un
                   <strong>test technique</strong>%s. Le test contient 10 questions à choix multiple
                   et ne prend que quelques minutes.</p>
                <div style="text-align:center;margin:28px 0">
                  <a href="%s" style="background:#22c55e;color:#fff;padding:13px 36px;border-radius:6px;
                     text-decoration:none;font-size:16px;font-weight:bold">
                    Passer au test
                  </a>
                </div>
                <p style="font-size:13px;color:#888">Ce lien est valable 48 heures et ne peut être utilisé
                   qu'une seule fois. Aucune création de compte n'est nécessaire.</p>
                <p style="font-size:13px;color:#888">SkillMatch AI — DecliTech Innovation</p>
              </div>
            </div>
            """.formatted(candidateName,
                          (jobTitle != null && !jobTitle.isBlank()) ? " (« " + jobTitle + " »)" : "",
                          testUrl);

        sendEmail(candidateEmail, "SkillMatch AI — Invitation à un test technique", html);
    }

    // =========================================================
    // Méthode générique d'envoi
    // =========================================================
    /**
     * Envoi générique d'un e-mail HTML (UTF-8). On attrape les exceptions
     * VOLONTAIREMENT : un échec d'envoi (SMTP indisponible...) ne doit pas
     * faire échouer l'action métier qui l'a déclenché (ex : une inscription
     * réussit même si l'e-mail à l'admin ne part pas).
     */
    private void sendEmail(String toEmail, String subject, String htmlContent) {
        try {
            MimeMessage message = mailSender.createMimeMessage();
            // true = message multipart (permet le HTML) ; "UTF-8" = accents OK.
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");
            helper.setFrom(senderEmail, "SkillMatch AI");
            helper.setTo(toEmail);
            helper.setSubject(subject);
            helper.setText(htmlContent, true); // true = contenu interprété en HTML
            mailSender.send(message);
            System.out.println("[EmailService] Email envoyé à " + toEmail);
        } catch (Exception e) {
            System.err.println("[EmailService] Erreur envoi email à " + toEmail + " : " + e.getMessage());
        }
    }
}
