import konstrukteur.Konstrukteur
import jasy.asset.Manager as AssetManager

@task
def build(regenerate = False):
	"""Generate source (development) version"""

	# Initialize assets
	assetManager = AssetManager.AssetManager(profile, session)

	# Build static website
	konstrukteur.Konstrukteur.build(regenerate)

	# Copy assets to build path
	assetManager.copyAssets()