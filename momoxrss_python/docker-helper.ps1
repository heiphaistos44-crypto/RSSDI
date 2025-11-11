# Script d'aide PowerShell pour RSSDI Docker
# Facilite le déploiement et le diagnostic des problèmes

param(
    [string]$Action = ""
)

# Couleurs pour les messages
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Blue"
    White = "White"
}

function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Colors.Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Colors.Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Colors.Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Colors.Red
}

# Vérification des prérequis
function Test-Requirements {
    Write-Status "Vérification des prérequis..."
    
    try {
        $null = Get-Command docker -ErrorAction Stop
        Write-Success "Docker est installé"
    }
    catch {
        Write-Error "Docker n'est pas installé ou non accessible"
        return $false
    }
    
    try {
        $null = Get-Command docker-compose -ErrorAction Stop
        Write-Success "Docker Compose est installé"
    }
    catch {
        Write-Error "Docker Compose n'est pas installé ou non accessible"
        return $false
    }
    
    return $true
}

# Vérification du fichier .env
function Test-EnvFile {
    Write-Status "Vérification du fichier .env..."
    
    if (-not (Test-Path ".env")) {
        Write-Warning "Fichier .env manquant, création depuis .env.example..."
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" ".env"
            Write-Warning "Pensez à configurer vos variables dans .env"
        }
        else {
            Write-Error "Fichier .env.example introuvable"
            return $false
        }
    }
    
    Write-Success "Fichier .env présent"
    return $true
}

# Test de connectivité réseau
function Test-NetworkConnectivity {
    Write-Status "Test de connectivité réseau..."
    
    try {
        $result = Test-Connection -ComputerName "registry-1.docker.io" -Count 1 -Quiet
        if ($result) {
            Write-Success "Connectivité vers Docker Hub OK"
            return $true
        }
        else {
            Write-Error "Problème de connectivité vers Docker Hub"
            Write-Warning "Vérifiez votre connexion internet ou utilisez un miroir Docker"
            return $false
        }
    }
    catch {
        Write-Error "Erreur lors du test de connectivité: $($_.Exception.Message)"
        return $false
    }
}

# Nettoyage des volumes et containers
function Invoke-Cleanup {
    Write-Status "Nettoyage des containers et volumes..."
    
    try {
        docker-compose down -v 2>$null
        docker system prune -f
        Write-Success "Nettoyage terminé"
    }
    catch {
        Write-Error "Erreur lors du nettoyage: $($_.Exception.Message)"
    }
}

# Démarrage avec diagnostic
function Start-WithDiagnostics {
    Write-Status "Démarrage avec diagnostics..."
    
    # Arrêt propre des services existants
    try {
        docker-compose down 2>$null
    }
    catch {}
    
    # Démarrage en mode verbeux
    Write-Status "Démarrage des services..."
    try {
        docker-compose up -d
        Write-Success "Services démarrés"
        
        # Attendre que MongoDB soit prêt
        Write-Status "Attente de MongoDB..."
        $maxAttempts = 30
        $attempt = 0
        
        do {
            Start-Sleep -Seconds 2
            $attempt++
            Write-Host "." -NoNewline
            
            try {
                $null = docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-Host ""
                    Write-Success "MongoDB est prêt"
                    break
                }
            }
            catch {}
            
        } while ($attempt -lt $maxAttempts)
        
        if ($attempt -ge $maxAttempts) {
            Write-Host ""
            Write-Warning "MongoDB pourrait ne pas être prêt"
        }
        
        # Vérifier l'application
        Write-Status "Vérification de l'application..."
        Start-Sleep -Seconds 5
        
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:3000/api/v1/stats" -TimeoutSec 10
            if ($response.StatusCode -eq 200) {
                Write-Success "Application accessible"
            }
        }
        catch {
            Write-Warning "L'application n'est pas encore accessible"
        }
        
    }
    catch {
        Write-Error "Échec du démarrage des services: $($_.Exception.Message)"
        return $false
    }
    
    return $true
}

# Affichage des logs
function Show-Logs {
    Write-Status "Affichage des logs..."
    docker-compose logs --tail=50 -f
}

# Statut des services
function Show-Status {
    Write-Status "Statut des services:"
    docker-compose ps
    
    Write-Status "Utilisation des ressources:"
    docker stats --no-stream
}

# Menu principal
function Show-Menu {
    Clear-Host
    Write-Host "=== RSSDI Docker Helper ===" -ForegroundColor $Colors.Blue
    Write-Host "1. Vérifier les prérequis"
    Write-Host "2. Démarrer les services (avec diagnostic)"
    Write-Host "3. Arrêter les services"
    Write-Host "4. Redémarrer les services"
    Write-Host "5. Voir les logs"
    Write-Host "6. Statut des services"
    Write-Host "7. Nettoyer (containers + volumes)"
    Write-Host "8. Test de connectivité"
    Write-Host "9. Quitter"
    Write-Host ""
}

# Fonction principale interactive
function Start-InteractiveMode {
    while ($true) {
        Show-Menu
        $choice = Read-Host "Choisissez une option [1-9]"
        
        switch ($choice) {
            "1" {
                Test-Requirements
                Test-EnvFile
            }
            "2" {
                if ((Test-Requirements) -and (Test-EnvFile)) {
                    Test-NetworkConnectivity
                    Start-WithDiagnostics
                }
            }
            "3" {
                docker-compose down
                Write-Success "Services arrêtés"
            }
            "4" {
                docker-compose restart
                Write-Success "Services redémarrés"
            }
            "5" {
                Show-Logs
            }
            "6" {
                Show-Status
            }
            "7" {
                Invoke-Cleanup
            }
            "8" {
                Test-NetworkConnectivity
            }
            "9" {
                Write-Status "Au revoir!"
                return
            }
            default {
                Write-Error "Option invalide"
            }
        }
        
        Write-Host ""
        Read-Host "Appuyez sur Entrée pour continuer..."
    }
}

# Point d'entrée principal
if ($Action -eq "") {
    Start-InteractiveMode
}
else {
    switch ($Action.ToLower()) {
        "check" {
            Test-Requirements
            Test-EnvFile
        }
        "start" {
            Start-WithDiagnostics
        }
        "stop" {
            docker-compose down
        }
        "clean" {
            Invoke-Cleanup
        }
        "logs" {
            Show-Logs
        }
        "status" {
            Show-Status
        }
        default {
            Write-Host "Usage: .\docker-helper.ps1 [check|start|stop|clean|logs|status]"
            exit 1
        }
    }
}