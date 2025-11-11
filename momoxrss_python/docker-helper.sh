#!/bin/bash

# Script d'aide pour RSSDI Docker
# Facilite le déploiement et le diagnostic des problèmes

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérification des prérequis
check_requirements() {
    print_status "Vérification des prérequis..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker n'est pas installé"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose n'est pas installé"
        exit 1
    fi
    
    print_success "Docker et Docker Compose sont installés"
}

# Vérification du fichier .env
check_env_file() {
    print_status "Vérification du fichier .env..."
    
    if [ ! -f ".env" ]; then
        print_warning "Fichier .env manquant, création depuis .env.example..."
        cp .env.example .env
        print_warning "Pensez à configurer vos variables dans .env"
    fi
    
    print_success "Fichier .env présent"
}

# Test de connectivité réseau
test_network() {
    print_status "Test de connectivité réseau..."
    
    if ping -c 1 registry-1.docker.io &> /dev/null; then
        print_success "Connectivité vers Docker Hub OK"
    else
        print_error "Problème de connectivité vers Docker Hub"
        print_warning "Vérifiez votre connexion internet ou utilisez un miroir Docker"
        return 1
    fi
}

# Nettoyage des volumes et containers
cleanup() {
    print_status "Nettoyage des containers et volumes..."
    
    docker-compose down -v 2>/dev/null || true
    docker system prune -f
    
    print_success "Nettoyage terminé"
}

# Démarrage avec diagnostic
start_with_diagnostics() {
    print_status "Démarrage avec diagnostics..."
    
    # Arrêt propre des services existants
    docker-compose down 2>/dev/null || true
    
    # Démarrage en mode verbeux
    print_status "Démarrage des services..."
    if docker-compose up -d; then
        print_success "Services démarrés"
        
        # Attendre que MongoDB soit prêt
        print_status "Attente de MongoDB..."
        for i in {1..30}; do
            if docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" &>/dev/null; then
                print_success "MongoDB est prêt"
                break
            fi
            echo -n "."
            sleep 2
        done
        
        # Vérifier l'application
        print_status "Vérification de l'application..."
        sleep 5
        if curl -f http://localhost:3000/api/v1/stats 2>/dev/null; then
            print_success "Application accessible"
        else
            print_warning "L'application n'est pas encore accessible"
        fi
        
    else
        print_error "Échec du démarrage des services"
        return 1
    fi
}

# Affichage des logs
show_logs() {
    print_status "Affichage des logs..."
    docker-compose logs --tail=50 -f
}

# Statut des services
status() {
    print_status "Statut des services:"
    docker-compose ps
    
    print_status "Utilisation des ressources:"
    docker stats --no-stream
}

# Menu principal
show_menu() {
    echo -e "${BLUE}=== RSSDI Docker Helper ===${NC}"
    echo "1. Vérifier les prérequis"
    echo "2. Démarrer les services (avec diagnostic)"
    echo "3. Arrêter les services"
    echo "4. Redémarrer les services"
    echo "5. Voir les logs"
    echo "6. Statut des services"
    echo "7. Nettoyer (containers + volumes)"
    echo "8. Test de connectivité"
    echo "9. Quitter"
    echo ""
}

# Fonction principale
main() {
    while true; do
        show_menu
        read -p "Choisissez une option [1-9]: " choice
        
        case $choice in
            1)
                check_requirements
                check_env_file
                ;;
            2)
                check_requirements
                check_env_file
                test_network
                start_with_diagnostics
                ;;
            3)
                docker-compose down
                print_success "Services arrêtés"
                ;;
            4)
                docker-compose restart
                print_success "Services redémarrés"
                ;;
            5)
                show_logs
                ;;
            6)
                status
                ;;
            7)
                cleanup
                ;;
            8)
                test_network
                ;;
            9)
                print_status "Au revoir!"
                exit 0
                ;;
            *)
                print_error "Option invalide"
                ;;
        esac
        
        echo ""
        read -p "Appuyez sur Entrée pour continuer..."
        clear
    done
}

# Exécution du script
if [ $# -eq 0 ]; then
    clear
    main
else
    # Permettre l'exécution de fonctions spécifiques
    case $1 in
        "check")
            check_requirements
            check_env_file
            ;;
        "start")
            start_with_diagnostics
            ;;
        "stop")
            docker-compose down
            ;;
        "clean")
            cleanup
            ;;
        "logs")
            show_logs
            ;;
        "status")
            status
            ;;
        *)
            echo "Usage: $0 [check|start|stop|clean|logs|status]"
            exit 1
            ;;
    esac
fi