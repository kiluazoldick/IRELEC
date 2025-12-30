# app.py
"""
IRELEC – Système de Gestion de Facturation d'Électricité (MVP)
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import tempfile
import os
from fpdf import FPDF
import base64

# Configuration de la page
st.set_page_config(
    page_title="IRELEC - Système de Facturation d'Électricité",
    page_icon="⚡",
    layout="wide"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .section-header {
        font-size: 1.8rem;
        color: #2563EB;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #2563EB;
    }
    .invoice-box {
        border: 2px solid #2563EB;
        border-radius: 10px;
        padding: 20px;
        background-color: #f0f9ff;
        margin: 20px 0;
    }
    .stButton>button {
        background-color: #2563EB;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 2rem;
    }
    .success-message {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Configuration base de données
def init_db():
    """Initialiser la base de données SQLite"""
    conn = sqlite3.connect('irelec.db')
    c = conn.cursor()
    
    # Table clients
    c.execute('''CREATE TABLE IF NOT EXISTS clients
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nom_complet TEXT NOT NULL,
                  numero_compteur TEXT UNIQUE NOT NULL,
                  numero_contrat TEXT UNIQUE NOT NULL,
                  localisation TEXT,
                  tarif REAL NOT NULL,
                  date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Table factures
    c.execute('''CREATE TABLE IF NOT EXISTS factures
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  client_id INTEGER,
                  numero_facture TEXT UNIQUE,
                  index_precedent REAL,
                  index_actuel REAL,
                  consommation REAL,
                  tarif REAL,
                  montant_total REAL,
                  date_facture TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (client_id) REFERENCES clients (id))''')
    
    conn.commit()
    conn.close()

# Initialiser la base de données
init_db()

# Fonctions d'aide pour la base de données
def get_db_connection():
    """Obtenir une connexion à la base de données"""
    return sqlite3.connect('irelec.db', check_same_thread=False)

def get_clients():
    """Récupérer tous les clients"""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM clients ORDER BY date_creation DESC", conn)
    conn.close()
    return df

def get_client_by_id(client_id):
    """Récupérer un client par ID"""
    conn = get_db_connection()
    df = pd.read_sql_query(f"SELECT * FROM clients WHERE id = {client_id}", conn)
    conn.close()
    return df.iloc[0] if not df.empty else None

def get_factures(client_id=None):
    """Récupérer les factures, optionnellement filtrées par client"""
    conn = get_db_connection()
    if client_id:
        query = """SELECT f.*, c.nom_complet, c.numero_compteur, c.numero_contrat 
                   FROM factures f 
                   JOIN clients c ON f.client_id = c.id 
                   WHERE f.client_id = ? 
                   ORDER BY f.date_facture DESC"""
        df = pd.read_sql_query(query, conn, params=(client_id,))
    else:
        query = """SELECT f.*, c.nom_complet, c.numero_compteur, c.numero_contrat 
                   FROM factures f 
                   JOIN clients c ON f.client_id = c.id 
                   ORDER BY f.date_facture DESC"""
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def sauvegarder_client(nom_complet, numero_compteur, numero_contrat, localisation, tarif):
    """Sauvegarder un nouveau client"""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO clients 
                     (nom_complet, numero_compteur, numero_contrat, localisation, tarif) 
                     VALUES (?, ?, ?, ?, ?)""",
                  (nom_complet, numero_compteur, numero_contrat, localisation, float(tarif)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def sauvegarder_facture(client_id, index_precedent, index_actuel, tarif):
    """Sauvegarder une facture"""
    consommation = index_actuel - index_precedent
    montant_total = consommation * tarif
    numero_facture = f"FACT-{datetime.now().strftime('%Y%m%d')}-{client_id:04d}"
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO factures 
                 (client_id, numero_facture, index_precedent, index_actuel, 
                  consommation, tarif, montant_total) 
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (client_id, numero_facture, index_precedent, index_actuel, 
               consommation, tarif, montant_total))
    conn.commit()
    conn.close()
    
    return {
        'numero_facture': numero_facture,
        'consommation': consommation,
        'montant_total': montant_total,
        'date_facture': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

# Fonction pour générer PDF (CORRIGÉE)
def generer_pdf(donnees_facture, info_client):
    """Générer une facture PDF"""
    pdf = FPDF()
    pdf.add_page()
    
    # Ajouter une police Unicode (DejaVu supporte UTF-8)
    try:
        pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
        pdf.add_font('DejaVu', 'B', 'DejaVuSansCondensed-Bold.ttf', uni=True)
        font_name = 'DejaVu'
    except:
        # Si les polices DejaVu ne sont pas disponibles, utiliser helvetica
        font_name = 'helvetica'
    
    # En-tête entreprise (avec tiret normal "-" au lieu de "–")
    pdf.set_font(font_name, 'B', 16)
    pdf.cell(0, 10, "IRELEC - Système de Facturation d'Electricité", align='C')
    pdf.ln(10)
    
    pdf.set_font(font_name, '', 12)
    pdf.cell(0, 10, "Fournisseur Officiel d'Electricité", align='C')
    pdf.ln(15)
    
    # Titre facture
    pdf.set_font(font_name, 'B', 14)
    pdf.cell(0, 10, "FACTURE D'ELECTRICITE", align='C')
    pdf.ln(15)
    
    # Détails facture
    pdf.set_font(font_name, '', 12)
    pdf.cell(0, 10, f"Numéro Facture: {donnees_facture['numero_facture']}")
    pdf.ln(10)
    pdf.cell(0, 10, f"Date: {donnees_facture['date_facture']}")
    pdf.ln(15)
    
    # Informations client
    pdf.set_font(font_name, 'B', 12)
    pdf.cell(0, 10, "Informations Client", align='L')
    pdf.ln(10)
    pdf.set_font(font_name, '', 12)
    
    infos = [
        f"Nom Complet: {info_client['nom_complet']}",
        f"Numéro Compteur: {info_client['numero_compteur']}",
        f"Numéro Contrat: {info_client['numero_contrat']}",
        f"Localisation: {info_client['localisation']}"
    ]
    
    for info in infos:
        pdf.cell(0, 8, info, align='L')
        pdf.ln(8)
    
    pdf.ln(10)
    
    # Détails facturation
    pdf.set_font(font_name, 'B', 12)
    pdf.cell(0, 10, "Détails de Facturation", align='L')
    pdf.ln(10)
    pdf.set_font(font_name, '', 12)
    
    details = [
        f"Index Précédent: {donnees_facture['index_precedent']:.2f} kWh",
        f"Index Actuel: {donnees_facture['index_actuel']:.2f} kWh",
        f"Consommation: {donnees_facture['consommation']:.2f} kWh",
        f"Tarif: {donnees_facture['tarif']:.2f} FCFA/kWh",
        "",
        f"MONTANT TOTAL: {donnees_facture['montant_total']:.2f} FCFA"
    ]
    
    for detail in details:
        pdf.cell(0, 8, detail, align='L')
        pdf.ln(8)
    
    pdf.ln(20)
    
    # Pied de page
    pdf.set_font(font_name, 'I', 10)
    pdf.cell(0, 10, "Merci d'utiliser les services IRELEC.", align='C')
    pdf.ln(5)
    pdf.cell(0, 10, "Pour toute question, contactez: support@irelec.cm", align='C')
    
    # Sauvegarder PDF dans fichier temporaire
    fichier_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.output(fichier_temp.name)
    return fichier_temp.name

# Application principale
def main():
    # En-tête
    st.markdown('<h1 class="main-header">⚡ IRELEC – Système de Gestion de Facturation d\'Électricité</h1>', unsafe_allow_html=True)
    
    # Barre latérale pour navigation
    st.sidebar.title("Navigation")
    section = st.sidebar.radio(
        "Aller à",
        ["Tableau de Bord", "Gestion Clients", "Consommation & Facturation", "Historique Factures"]
    )
    
    # État de session
    if 'client_selectionne_id' not in st.session_state:
        st.session_state.client_selectionne_id = None
    if 'facture_actuelle' not in st.session_state:
        st.session_state.facture_actuelle = None
    if 'facture_generee' not in st.session_state:
        st.session_state.facture_generee = None
    
    # TABLEAU DE BORD
    if section == "Tableau de Bord":
        st.markdown('<h2 class="section-header">📊 Tableau de Bord</h2>', unsafe_allow_html=True)
        
        # Statistiques
        col1, col2, col3 = st.columns(3)
        
        with col1:
            clients_df = get_clients()
            st.metric("Total Clients", len(clients_df))
        
        with col2:
            factures_df = get_factures()
            st.metric("Total Factures", len(factures_df))
        
        with col3:
            revenu_total = factures_df['montant_total'].sum() if not factures_df.empty else 0
            st.metric("Revenu Total", f"{revenu_total:,.2f} FCFA")
        
        # Activité récente
        st.markdown("### Activité Récente")
        if not factures_df.empty:
            factures_recentes = factures_df.head(5)
            # Renommer les colonnes pour un affichage plus clair
            display_df = factures_recentes[['numero_facture', 'nom_complet', 'date_facture', 'montant_total']].copy()
            display_df.columns = ['Numéro Facture', 'Client', 'Date', 'Montant']
            st.dataframe(display_df)
        else:
            st.info("Aucune facture générée pour le moment.")
    
    # GESTION CLIENTS
    elif section == "Gestion Clients":
        st.markdown('<h2 class="section-header">👥 Gestion Clients</h2>', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Ajouter Nouveau Client", "Voir Tous les Clients"])
        
        with tab1:
            st.markdown("### Ajouter Nouveau Client")
            
            with st.form("formulaire_client"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nom_complet = st.text_input("Nom Complet *", placeholder="Jean Dupont")
                    numero_compteur = st.text_input("Numéro Compteur *", placeholder="COMP-123456")
                    numero_contrat = st.text_input("Numéro Contrat *", placeholder="CNT-789012")
                
                with col2:
                    localisation = st.text_input("Localisation", placeholder="Douala, Bonaberi")
                    tarif = st.number_input("Tarif (FCFA/kWh) *", min_value=0.0, value=75.0, step=0.1)
                
                soumis = st.form_submit_button("Ajouter Client")
                
                if soumis:
                    if all([nom_complet, numero_compteur, numero_contrat]):
                        succes = sauvegarder_client(nom_complet, numero_compteur, numero_contrat, localisation, tarif)
                        if succes:
                            st.markdown('<div class="success-message">✅ Client ajouté avec succès!</div>', unsafe_allow_html=True)
                        else:
                            st.error("Erreur: Numéro de compteur ou contrat existe déjà!")
                    else:
                        st.error("Veuillez remplir tous les champs obligatoires (*)")
        
        with tab2:
            st.markdown("### Base de Données Clients")
            clients_df = get_clients()
            
            if not clients_df.empty:
                # Afficher tableau clients
                df_affiche = clients_df[['nom_complet', 'numero_compteur', 'numero_contrat', 'localisation', 'tarif', 'date_creation']]
                df_affiche.columns = ['Nom Complet', 'Numéro Compteur', 'Numéro Contrat', 'Localisation', 'Tarif (FCFA/kWh)', 'Date Création']
                st.dataframe(df_affiche)
                
                # Sélection client
                st.markdown("### Sélectionner Client pour Opérations")
                options_clients = {f"{row['nom_complet']} ({row['numero_compteur']})": row['id'] 
                                   for _, row in clients_df.iterrows()}
                
                client_selectionne = st.selectbox(
                    "Choisir un client:",
                    options=list(options_clients.keys()),
                    index=0 if options_clients else None
                )
                
                if client_selectionne:
                    st.session_state.client_selectionne_id = options_clients[client_selectionne]
                    st.info(f"✅ Client sélectionné: {client_selectionne}")
            else:
                st.info("Aucun client dans la base de données. Veuillez ajouter un client d'abord.")
    
    # CONSOMMATION & FACTURATION
    elif section == "Consommation & Facturation":
        st.markdown('<h2 class="section-header">💡 Consommation & Facturation</h2>', unsafe_allow_html=True)
        
        # Récupérer clients pour sélection
        clients_df = get_clients()
        
        if clients_df.empty:
            st.warning("Aucun client disponible. Veuillez ajouter des clients d'abord.")
            return
        
        # Sélection client
        options_clients = {f"{row['nom_complet']} (Compteur: {row['numero_compteur']})": row['id'] 
                           for _, row in clients_df.iterrows()}
        
        label_client_selectionne = st.selectbox(
            "Sélectionner Client:",
            options=list(options_clients.keys()),
            key="selection_facturation"
        )
        
        if label_client_selectionne:
            client_id = options_clients[label_client_selectionne]
            info_client = get_client_by_id(client_id)
            
            if info_client is not None:
                st.session_state.client_selectionne_id = client_id
                
                # Afficher info client
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"**Nom:** {info_client['nom_complet']}")
                with col2:
                    st.info(f"**Compteur:** {info_client['numero_compteur']}")
                with col3:
                    st.info(f"**Tarif:** {info_client['tarif']} FCFA/kWh")
                
                # Formulaire de facturation
                st.markdown("### Entrer les Index du Compteur")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    index_precedent = st.number_input("Index Précédent (kWh)", 
                                                      min_value=0.0, value=0.0, step=0.1,
                                                      key="index_precedent")
                with col2:
                    index_actuel = st.number_input("Index Actuel (kWh)", 
                                                   min_value=0.0, 
                                                   value=0.0, step=0.1,
                                                   key="index_actuel")
                
                # Calculer la consommation
                if st.button("Calculer Facture", key="calculer_facture"):
                    if index_actuel > index_precedent:
                        consommation = index_actuel - index_precedent
                        montant = consommation * info_client['tarif']
                        
                        # Sauvegarder dans l'état de session
                        st.session_state.facture_actuelle = {
                            'info_client': info_client,
                            'index_precedent': index_precedent,
                            'index_actuel': index_actuel,
                            'consommation': consommation,
                            'tarif': info_client['tarif'],
                            'montant_total': montant
                        }
                    else:
                        st.error("L'index actuel doit être supérieur à l'index précédent!")
                
                # Afficher calcul si disponible
                if st.session_state.facture_actuelle:
                    facture = st.session_state.facture_actuelle
                    
                    st.markdown('<div class="invoice-box">', unsafe_allow_html=True)
                    st.markdown("### 📋 Calcul de la Facture")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Index Précédent:** {facture['index_precedent']:.2f} kWh")
                        st.write(f"**Index Actuel:** {facture['index_actuel']:.2f} kWh")
                        st.write(f"**Consommation:** {facture['consommation']:.2f} kWh")
                    
                    with col2:
                        st.write(f"**Tarif:** {facture['tarif']:.2f} FCFA/kWh")
                        st.markdown(f"**Montant Total:** {facture['montant_total']:.2f} FCFA")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Bouton générer facture
                    if st.button("📄 Générer Facture", key="generer_facture"):
                        try:
                            donnees_facture = sauvegarder_facture(
                                client_id, 
                                facture['index_precedent'], 
                                facture['index_actuel'], 
                                facture['tarif']
                            )
                            
                            # Sauvegarder les données pour l'affichage
                            st.session_state.facture_generee = {
                                'info_client': facture['info_client'],
                                'donnees_facture': donnees_facture,
                                'index_precedent': facture['index_precedent'],
                                'index_actuel': facture['index_actuel'],
                                'consommation': facture['consommation'],
                                'tarif': facture['tarif'],
                                'montant_total': facture['montant_total']
                            }
                            
                            # Afficher facture
                            afficher_facture(
                                st.session_state.facture_generee['info_client'],
                                st.session_state.facture_generee['index_precedent'],
                                st.session_state.facture_generee['index_actuel'],
                                st.session_state.facture_generee['consommation'],
                                st.session_state.facture_generee['tarif'],
                                st.session_state.facture_generee['montant_total'],
                                st.session_state.facture_generee['donnees_facture']['numero_facture']
                            )
                        except Exception as e:
                            st.error(f"Erreur lors de la génération de la facture: {str(e)}")
                elif st.session_state.facture_generee:
                    # Afficher la dernière facture générée
                    facture = st.session_state.facture_generee
                    afficher_facture(
                        facture['info_client'],
                        facture['index_precedent'],
                        facture['index_actuel'],
                        facture['consommation'],
                        facture['tarif'],
                        facture['montant_total'],
                        facture['donnees_facture']['numero_facture']
                    )
    
    # HISTORIQUE FACTURES
    elif section == "Historique Factures":
        st.markdown('<h2 class="section-header">📜 Historique des Factures</h2>', unsafe_allow_html=True)
        
        # Filtres
        col1, col2 = st.columns(2)
        
        with col1:
            clients_df = get_clients()
            if not clients_df.empty:
                options_filtre = ["Tous les Clients"] + \
                                [f"{row['nom_complet']} ({row['numero_compteur']})" 
                                 for _, row in clients_df.iterrows()]
                filtre_client = st.selectbox("Filtrer par Client:", options_filtre)
            else:
                filtre_client = "Tous les Clients"
        
        with col2:
            # Filtre mois (option bonus)
            options_mois = ["Tous les Mois"] + [datetime(2024, i, 1).strftime("%B %Y") for i in range(1, 13)]
            mois_selectionne = st.selectbox("Filtrer par Mois:", options_mois)
        
        # Récupérer factures selon filtres
        if filtre_client == "Tous les Clients":
            factures_df = get_factures()
        else:
            # Extraire ID client
            nom_client = filtre_client.split(" (")[0]
            client_id = clients_df[clients_df['nom_complet'] == nom_client]['id'].values[0]
            factures_df = get_factures(client_id)
        
        # Appliquer filtre mois si sélectionné
        if mois_selectionne != "Tous les Mois":
            mois_num = datetime.strptime(mois_selectionne, "%B %Y").month
            annee = datetime.strptime(mois_selectionne, "%B %Y").year
            factures_df['date_facture'] = pd.to_datetime(factures_df['date_facture'])
            factures_df = factures_df[
                (factures_df['date_facture'].dt.month == mois_num) & 
                (factures_df['date_facture'].dt.year == annee)
            ]
        
        # Afficher factures
        if not factures_df.empty:
            # Statistiques
            total_factures = len(factures_df)
            montant_total = factures_df['montant_total'].sum()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Nombre de Factures", total_factures)
            with col2:
                st.metric("Montant Total", f"{montant_total:,.2f} FCFA")
            
            # Afficher tableau
            colonnes_affiche = ['numero_facture', 'nom_complet', 'numero_compteur', 
                                'date_facture', 'consommation', 'montant_total']
            df_affiche = factures_df[colonnes_affiche].copy()
            df_affiche['date_facture'] = pd.to_datetime(df_affiche['date_facture']).dt.strftime('%Y-%m-%d')
            df_affiche.columns = ['Numéro Facture', 'Client', 'Numéro Compteur', 'Date', 'Consommation (kWh)', 'Montant (FCFA)']
            
            st.dataframe(df_affiche, use_container_width=True)
            
            # Option voir facture détaillée
            st.markdown("### Voir Facture Détaillée")
            numeros_factures = factures_df['numero_facture'].tolist()
            facture_selectionnee = st.selectbox("Sélectionner Facture:", numeros_factures)
            
            if facture_selectionnee:
                facture = factures_df[factures_df['numero_facture'] == facture_selectionnee].iloc[0]
                client_info = get_client_by_id(facture['client_id'])
                info_client = {
                    'nom_complet': facture['nom_complet'],
                    'numero_compteur': facture['numero_compteur'],
                    'numero_contrat': facture['numero_contrat'],
                    'localisation': client_info['localisation']
                }
                
                afficher_facture(
                    info_client,
                    facture['index_precedent'],
                    facture['index_actuel'],
                    facture['consommation'],
                    facture['tarif'],
                    facture['montant_total'],
                    facture['numero_facture'],
                    facture['date_facture']
                )
        else:
            st.info("Aucune facture trouvée avec les filtres sélectionnés.")

def afficher_facture(info_client, index_precedent, index_actuel, consommation, 
                     tarif, montant_total, numero_facture, date_facture=None):
    """Afficher facture dans une boîte formatée avec option PDF"""
    if date_facture is None:
        date_facture = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    st.markdown('<div class="invoice-box">', unsafe_allow_html=True)
    
    # En-tête facture
    st.markdown("""
    <div style="text-align: center;">
        <h2 style="color: #1E3A8A;">IRELEC – Système de Facturation d'Électricité</h2>
        <h3 style="color: #2563EB;">FACTURE D'ÉLECTRICITÉ</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Détails facture
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Numéro Facture:** {numero_facture}")
        st.markdown(f"**Date:** {date_facture}")
    
    with col2:
        st.markdown(f"**Numéro Compteur:** {info_client['numero_compteur']}")
        st.markdown(f"**Numéro Contrat:** {info_client['numero_contrat']}")
    
    st.markdown("---")
    
    # Informations client
    st.markdown("### Informations Client")
    st.markdown(f"**Nom Complet:** {info_client['nom_complet']}")
    st.markdown(f"**Localisation:** {info_client.get('localisation', 'Non spécifié')}")
    
    st.markdown("---")
    
    # Détails facturation
    st.markdown("### Détails de Facturation")
    
    donnees_facturation = {
        "Index Précédent": f"{index_precedent:.2f} kWh",
        "Index Actuel": f"{index_actuel:.2f} kWh",
        "Consommation": f"{consommation:.2f} kWh",
        "Prix par kWh": f"{tarif:.2f} FCFA",
        "Montant Total": f"{montant_total:.2f} FCFA"
    }
    
    for cle, valeur in donnees_facturation.items():
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"**{cle}:**")
        with col2:
            st.markdown(valeur)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Données pour PDF
    donnees_facture = {
        'numero_facture': numero_facture,
        'date_facture': date_facture,
        'index_precedent': index_precedent,
        'index_actuel': index_actuel,
        'consommation': consommation,
        'tarif': tarif,
        'montant_total': montant_total
    }
    
    # Bouton pour générer PDF
    if st.button("📥 Générer PDF", key=f"pdf_{numero_facture}"):
        with st.spinner("Génération du PDF en cours..."):
            try:
                # Générer PDF
                chemin_pdf = generer_pdf(donnees_facture, info_client)
                
                with open(chemin_pdf, "rb") as fichier_pdf:
                    bytes_pdf = fichier_pdf.read()
                
                # Encoder en base64 pour le téléchargement
                b64 = base64.b64encode(bytes_pdf).decode()
                href = f'<a href="data:application/octet-stream;base64,{b64}" download="{numero_facture}.pdf">Cliquez ici pour télécharger</a>'
                
                st.markdown(f"**Facture prête !** {href}", unsafe_allow_html=True)
                
                # Nettoyer fichier temporaire
                os.unlink(chemin_pdf)
                
            except Exception as e:
                st.error(f"Erreur lors de la génération du PDF: {str(e)}")
                st.info("Solution alternative: Essayez d'installer les polices DejaVu ou utilisez une police standard.")

if __name__ == "__main__":
    main()