# Media-free sample catalog

The public sample contains no downloaded reaction media. Start with
`examples/catalog-empty.json`, then add only JPEG or GIF files you created or
have the right to use in an external operator media directory. Catalog entries
follow `contracts/catalog.schema.json`; the bridge derives and validates media
metadata rather than trusting operator-supplied hashes or MIME labels.

Never commit the populated catalog, its captions, or its media to this source
tree. Run `sol-peanut-gallery --config /path/to/bridge.json validate-catalog`
after every catalog change.
