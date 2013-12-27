import konstrukteur.Konstrukteur
import jasy.asset.Manager2 as AssetManager

@task
def build(regenerate = False):
	"""Generate source (development) version"""

	# Initialize assets
	AssetManager.AssetManager(profile, session)

	# Build static website
	konstrukteur.Konstrukteur.build(regenerate)
