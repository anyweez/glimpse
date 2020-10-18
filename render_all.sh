for file in worlds/*.json;
do
    echo "Rendering $file..."
    node dist/renderer/app.js $file
done;